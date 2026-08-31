# Password hashing (bcrypt via passlib) + JWT session tokens.
#
# Passwords are hashed one-way and never decrypted; "login" means re-hashing
# the submitted password and comparing hashes, not recovering the plaintext.
#
# The JWT is what actually closes the gap flagged earlier: previously a
# request just claimed an X-User-Id with nothing checking whether that claim
# was ever backed by a real login. Now the server signs a token at login
# containing the user id, and every subsequent request must present that
# same signed token — a request can no longer claim to be a different user
# than the one who actually authenticated, since it can't forge a valid
# signature without jwt_secret_key.

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: uuid.UUID) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    """Returns the user id encoded in the token. Raises jwt.PyJWTError (expired,
    bad signature, malformed, etc.) on anything invalid — callers turn that
    into a 401, never a silent fallback."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return uuid.UUID(payload["sub"])
