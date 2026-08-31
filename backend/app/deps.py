# Shared FastAPI dependencies — DB session, current acting user (via JWT), and the
# tenant-isolation guards every organization- or document-scoped route depends on.

import uuid
from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.crud.user import get_user
from app.database import SessionLocal
from app.models.document import Document
from app.models.user import User
from app.security import decode_access_token

# auto_error=False so a MISSING Authorization header becomes 401 below rather than
# FastAPI's default 403. The distinction matters to callers: the frontend treats 401
# as "session gone, log out" (see throwForResponse in app.js) and 403 as "you may not
# do this" — a missing token is the former.
_bearer_scheme = HTTPBearer(bearerFormat="JWT", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid session token")

    user = get_user(db, user_id)
    if user is None:
        # Token was validly signed but the account it points to is gone
        # (e.g. deleted after the token was issued).
        raise HTTPException(status_code=401, detail="Account no longer exists")
    return user


# ==========================================================================
# Tenant isolation
# ==========================================================================
#
# get_current_user proves *who* is calling. It says nothing about whether they may
# touch the organization named in the path — and until these guards existed, nothing
# else did either: `user.organization_id` was never compared against the request,
# anywhere in the codebase. Isolation was enforced only by the frontend choosing
# which UUID to send, so any authenticated user could read, write or delete another
# organization's evidence by editing the URL.
#
# The rule: auditors work across organizations by design (they pick one from a list
# — see frontend/app.js showOrganizationsList). Developers are scoped to their own.


def _may_access_org(user: User, organization_id: uuid.UUID) -> bool:
    return user.persona == "auditor" or user.organization_id == organization_id


def _forbid() -> None:
    # Deliberately does not say whether the organization exists — that would let a
    # caller enumerate organizations by probing UUIDs.
    raise HTTPException(status_code=403, detail="You do not have access to this organization")


def require_org_access(
    organization_id: uuid.UUID, current_user: User = Depends(get_current_user)
) -> User:
    """For routes with `organization_id` in the path. FastAPI resolves that path
    parameter into this dependency, so a route only has to depend on this instead of
    get_current_user and the check can't be forgotten per-route."""
    if not _may_access_org(current_user, organization_id):
        _forbid()
    return current_user


def require_document_access(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """For routes keyed by a single document. Resolves the document to its owning
    organization, then applies the same rule.

    A missing document is 404 whether or not the caller would have been allowed to
    see it — the alternative leaks existence.
    """
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if not _may_access_org(current_user, document.organization_id):
        _forbid()
    return current_user


def require_document_group_access(
    document_group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """For version-history routes, which are keyed by group rather than by a single
    version. Every version in a group belongs to the same organization, so any one of
    them answers the question."""
    document = (
        db.query(Document).filter(Document.document_group_id == document_group_id).first()
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if not _may_access_org(current_user, document.organization_id):
        _forbid()
    return current_user


def require_run_access(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """For routes keyed by an analysis run. A run belongs to one organization, so
    without this a developer could read another organization's coverage report — and
    therefore the shape of its evidence — just by holding a run id."""
    from app.models.analysis_run import AnalysisRun

    run = db.get(AnalysisRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not _may_access_org(current_user, run.organization_id):
        _forbid()
    return current_user


# ==========================================================================
# Auditor-only surfaces
# ==========================================================================
#
# Assessment belongs to the auditor. Developers submit evidence; they don't see how
# it was graded — the scores are unreviewed model output, and presenting them to the
# submitter both implies a verdict nobody has issued and invites wording tweaked
# until the number rises.
#
# These compose onto the tenant guards above rather than replacing them, so the
# organization check still applies. That matters if the auditor rule is ever
# narrowed (e.g. auditors scoped to assigned organizations) — the persona check
# alone would silently stop being sufficient.


def _require_auditor_persona(user: User) -> User:
    if user.persona != "auditor":
        raise HTTPException(status_code=403, detail="Only auditors can view assessment results")
    return user


def require_auditor(current_user: User = Depends(get_current_user)) -> User:
    """Auditor-only, with no organization in the path."""
    return _require_auditor_persona(current_user)


def require_auditor_org_access(current_user: User = Depends(require_org_access)) -> User:
    """Auditor-only, for routes with `organization_id` in the path."""
    return _require_auditor_persona(current_user)


def require_auditor_document_access(current_user: User = Depends(require_document_access)) -> User:
    """Auditor-only, for routes keyed by a single document."""
    return _require_auditor_persona(current_user)
