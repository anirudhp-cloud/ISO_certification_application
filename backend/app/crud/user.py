# DB access functions for User.

import uuid

from sqlalchemy.orm import Session

from app.models.user import User


def create_user(db: Session, *, organization_id: uuid.UUID, name: str, email: str, persona: str, password_hash: str) -> User:
    user = User(organization_id=organization_id, name=name, email=email, persona=persona, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).one_or_none()
