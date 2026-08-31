# Pydantic schemas for registration/login.

import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, model_validator

from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    persona: Literal["developer", "auditor"]
    # Exactly one of these: join an existing organization, or create a new one.
    organization_id: uuid.UUID | None = None
    organization_name: str | None = None

    @model_validator(mode="after")
    def exactly_one_organization_field(self) -> "RegisterRequest":
        if bool(self.organization_id) == bool(self.organization_name):
            raise ValueError("Provide exactly one of organization_id or organization_name")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
