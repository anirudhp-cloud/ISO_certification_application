# Organization endpoints.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.organization import create_organization, list_organizations
from app.deps import get_db
from app.schemas.organization import OrganizationCreate, OrganizationRead

router = APIRouter()


@router.get("", response_model=list[OrganizationRead])
def get_organizations(db: Session = Depends(get_db)) -> list[OrganizationRead]:
    return list_organizations(db)


@router.post("", response_model=OrganizationRead)
def post_organization(payload: OrganizationCreate, db: Session = Depends(get_db)) -> OrganizationRead:
    return create_organization(db, name=payload.name)
