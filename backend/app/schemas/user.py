# Pydantic schema for User read. Creation happens only via
# POST /api/auth/register (see schemas/auth.py) — no plain create-user
# schema here, since that would bypass the password/auth flow.

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    email: str
    persona: str
    created_at: datetime
