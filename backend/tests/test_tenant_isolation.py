# Tenant isolation tests.
#
# Before these guards, `user.organization_id` was never compared against the
# organization named in a request — not once, anywhere in the codebase. Isolation
# rested entirely on the frontend choosing which UUID to send, so any authenticated
# user could read, write or delete another organization's evidence by editing the URL.
# Seven endpoints additionally required no login at all, including the one that
# returns a document's full extracted text.
#
# The rule under test: auditors work across organizations by design (they pick one
# from a list); developers are confined to their own.

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.deps import (
    _may_access_org,
    require_auditor,
    require_auditor_document_access,
    require_auditor_org_access,
    require_document_access,
    require_document_group_access,
    require_org_access,
    require_run_access,
)

ORG_A = uuid.uuid4()
ORG_B = uuid.uuid4()

# Both structural tests below parse the route modules the same way.
ROUTE_SPLIT = r"\n(?=@router\.)"
ROUTE_DECORATOR = r'@router\.(get|post|patch|put|delete)\(\s*\n?\s*"([^"]*)"'


def _user(persona, organization_id):
    return SimpleNamespace(id=uuid.uuid4(), persona=persona, organization_id=organization_id)


class _FakeSession:
    """Returns a stored object for db.get(), and supports the single first() query
    require_document_group_access makes."""

    def __init__(self, obj=None):
        self._obj = obj

    def get(self, model, pk):
        return self._obj

    def query(self, *a, **k):
        return self

    def filter(self, *a, **k):
        return self

    def first(self):
        return self._obj


# --- the rule itself -------------------------------------------------------


def test_a_developer_may_only_reach_their_own_organization():
    developer = _user("developer", ORG_A)
    assert _may_access_org(developer, ORG_A)
    assert not _may_access_org(developer, ORG_B)


def test_an_auditor_may_reach_any_organization():
    """Auditors review across organizations by design — that's the whole
    organizations-list screen."""
    auditor = _user("auditor", ORG_A)
    assert _may_access_org(auditor, ORG_A)
    assert _may_access_org(auditor, ORG_B)


# --- organization-scoped routes -------------------------------------------


def test_org_route_rejects_a_developer_from_another_organization():
    with pytest.raises(HTTPException) as exc:
        require_org_access(ORG_B, current_user=_user("developer", ORG_A))
    assert exc.value.status_code == 403


def test_org_route_admits_the_owning_developer_and_any_auditor():
    assert require_org_access(ORG_A, current_user=_user("developer", ORG_A)) is not None
    assert require_org_access(ORG_B, current_user=_user("auditor", ORG_A)) is not None


def test_the_refusal_does_not_reveal_whether_the_organization_exists():
    """Saying "no such organization" vs "not yours" would let a caller enumerate
    organizations by probing UUIDs."""
    with pytest.raises(HTTPException) as exc:
        require_org_access(ORG_B, current_user=_user("developer", ORG_A))
    assert "do not have access" in exc.value.detail
    assert str(ORG_B) not in exc.value.detail


# --- document-scoped routes ----------------------------------------------


def test_document_route_resolves_the_owning_organization():
    document = SimpleNamespace(id=uuid.uuid4(), organization_id=ORG_A)
    db = _FakeSession(document)

    assert require_document_access(document.id, _user("developer", ORG_A), db) is not None
    with pytest.raises(HTTPException) as exc:
        require_document_access(document.id, _user("developer", ORG_B), db)
    assert exc.value.status_code == 403


def test_a_missing_document_is_404_not_403():
    """404 regardless of whether the caller would have been allowed to see it —
    the alternative leaks existence."""
    with pytest.raises(HTTPException) as exc:
        require_document_access(uuid.uuid4(), _user("developer", ORG_A), _FakeSession(None))
    assert exc.value.status_code == 404


def test_version_history_is_scoped_by_the_groups_organization():
    document = SimpleNamespace(id=uuid.uuid4(), organization_id=ORG_A)
    db = _FakeSession(document)

    assert require_document_group_access(uuid.uuid4(), _user("auditor", ORG_B), db) is not None
    with pytest.raises(HTTPException) as exc:
        require_document_group_access(uuid.uuid4(), _user("developer", ORG_B), db)
    assert exc.value.status_code == 403


def test_a_missing_document_group_is_404():
    with pytest.raises(HTTPException) as exc:
        require_document_group_access(uuid.uuid4(), _user("developer", ORG_A), _FakeSession(None))
    assert exc.value.status_code == 404


# --- run-scoped routes ---------------------------------------------------


def test_run_route_is_scoped_so_a_run_id_alone_grants_nothing():
    """A coverage report reveals the shape of an organization's evidence, so holding a
    run id must not be enough."""
    run = SimpleNamespace(id=uuid.uuid4(), organization_id=ORG_A)
    db = _FakeSession(run)

    assert require_run_access(run.id, _user("developer", ORG_A), db) is not None
    with pytest.raises(HTTPException) as exc:
        require_run_access(run.id, _user("developer", ORG_B), db)
    assert exc.value.status_code == 403


def test_a_missing_run_is_404():
    with pytest.raises(HTTPException) as exc:
        require_run_access(uuid.uuid4(), _user("developer", ORG_A), _FakeSession(None))
    assert exc.value.status_code == 404


# --- no route is left open ----------------------------------------------


def test_every_route_is_either_guarded_or_deliberately_pre_auth():
    """A structural check, so a new route can't quietly ship unguarded. The only
    endpoints allowed to be open are the ones the login screen needs before a token
    exists: register, login, and the organization list that fills the register
    dropdown."""
    import re
    from pathlib import Path

    guards = (
        "require_org_access",
        "require_document_access",
        "require_document_group_access",
        "require_run_access",
        # Auditor-only surfaces. These compose onto the tenant guards above, so a
        # route depending on one is org-checked as well as persona-checked.
        "require_auditor",
        "require_auditor_org_access",
        "require_auditor_document_access",
    )
    allowed_open = {("POST", "/register"), ("POST", "/login"), ("GET", ""), ("POST", "")}

    open_routes = []
    routes_dir = Path(__file__).resolve().parent.parent / "app" / "api" / "routes"
    for path in routes_dir.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for block in re.split(ROUTE_SPLIT, source):
            match = re.match(ROUTE_DECORATOR, block)
            if not match:
                continue
            verb, route = match.group(1).upper(), match.group(2)
            signature = block[: block.find(") ->")] if ") ->" in block else block[:900]
            if (verb, route) in allowed_open:
                continue
            if any(g in signature for g in guards) or "get_current_user" in signature:
                continue
            open_routes.append(f"{verb} {route} ({path.name})")

    assert not open_routes, f"unauthenticated route(s): {open_routes}"


# --- assessment is auditor-only -------------------------------------------
#
# Developers submit evidence; how it was graded is the auditor's judgement, and the
# scores are unreviewed model output until an auditor confirms them. Showing them to
# the submitter would imply a verdict nobody has issued, and invite wording tuned
# until the number rises.


def test_a_developer_cannot_reach_assessment_results_even_for_their_own_organization():
    developer = _user("developer", ORG_A)

    with pytest.raises(HTTPException) as exc:
        require_auditor(current_user=developer)
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException):
        require_auditor_org_access(current_user=developer)

    with pytest.raises(HTTPException):
        require_auditor_document_access(current_user=developer)


def test_an_auditor_reaches_assessment_results():
    auditor = _user("auditor", ORG_A)
    assert require_auditor(current_user=auditor) is auditor
    assert require_auditor_org_access(current_user=auditor) is auditor
    assert require_auditor_document_access(current_user=auditor) is auditor


def test_the_auditor_guards_compose_onto_the_tenant_guards():
    """require_auditor_org_access depends on require_org_access, so the organization
    check still runs. This matters if auditors are ever scoped to assigned
    organizations — the persona check alone would silently stop being enough."""
    import inspect

    from app.deps import require_auditor_org_access as guard

    depends_on = inspect.signature(guard).parameters["current_user"].default
    assert depends_on.dependency is require_org_access


def test_developer_facing_routes_are_not_auditor_gated():
    """The developer must keep their own documents, versions, extracted text and
    review comments — otherwise they cannot see what they submitted at all."""
    import re
    from pathlib import Path

    routes_dir = Path(__file__).resolve().parent.parent / "app" / "api" / "routes"
    must_stay_open_to_developers = {
        ("GET", "/organizations/{organization_id}/standards/{standard}/documents"),
        ("GET", "/documents/{document_id}/extraction"),
        ("GET", "/documents/{document_group_id}/versions"),
        ("GET", "/documents/{document_id}/comments"),
    }

    over_gated = []
    for path in routes_dir.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for block in re.split(ROUTE_SPLIT, source):
            match = re.match(ROUTE_DECORATOR, block)
            if not match:
                continue
            key = (match.group(1).upper(), match.group(2))
            signature = block[: block.find(") ->")] if ") ->" in block else block[:900]
            if key in must_stay_open_to_developers and "require_auditor" in signature:
                over_gated.append(f"{key[0]} {key[1]}")

    assert not over_gated, f"developer-facing route(s) gated to auditors: {over_gated}"
