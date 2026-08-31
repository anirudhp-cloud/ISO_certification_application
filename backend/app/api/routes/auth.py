# Registration/login endpoints. Passwords are hashed (bcrypt) at registration
# and verified by re-hashing at login — never decrypted, never stored or
# returned in plaintext. Both endpoints issue a signed JWT on success; every
# other endpoint that needs to know "who is this request from" verifies that
# token (see deps.get_current_user) instead of trusting a claimed user id.

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.organization import create_organization, get_organization
from app.crud.user import create_user, get_user_by_email
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.security import create_access_token, hash_password, verify_password

logger = logging.getLogger(f"iso_platform.{__name__}")
router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if payload.organization_id is not None:
        org = get_organization(db, payload.organization_id)
        if org is None:
            raise HTTPException(status_code=404, detail="No organization with that id")
    else:
        org = create_organization(db, name=payload.organization_name)

    try:
        user = create_user(
            db,
            organization_id=org.id,
            name=payload.name,
            email=payload.email,
            persona=payload.persona,
            password_hash=hash_password(payload.password),
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with that email already exists")

    logger.info("registered: user=%s org=%s persona=%s", user.id, org.id, user.persona)
    return TokenResponse(access_token=create_access_token(user.id), user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    # Same generic error whether the email doesn't exist or the password is
    # wrong — distinguishing the two would let an attacker enumerate accounts.
    if user is None or not verify_password(payload.password, user.password_hash):
        logger.warning("login failed for email=%s", payload.email)
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    logger.info("login: user=%s", user.id)
    return TokenResponse(access_token=create_access_token(user.id), user=user)


@router.get("/me", response_model=UserRead)
def get_current_user_identity(current_user: User = Depends(get_current_user)) -> UserRead:
    # Lets the frontend confirm a stored token still corresponds to a real,
    # still-existing account before trusting a cached session — a token from
    # a user/account that was since removed (e.g. test-data cleanup) must not
    # let the UI keep rendering that identity as if it were still valid.
    return current_user
