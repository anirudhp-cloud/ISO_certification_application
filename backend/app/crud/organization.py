# DB access functions for Organization.

import uuid

from sqlalchemy.orm import Session

from app.models.organization import Organization


def create_organization(db: Session, name: str) -> Organization:
    org = Organization(name=name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def list_organizations(db: Session) -> list[Organization]:
    return db.query(Organization).order_by(Organization.name).all()


def get_organization(db: Session, organization_id: uuid.UUID) -> Organization | None:
    return db.get(Organization, organization_id)
