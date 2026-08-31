# Pydantic schemas for DocumentReviewComment.

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReviewCommentCreate(BaseModel):
    comment_text: str


class ReviewCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    reviewed_by: uuid.UUID
    reviewed_by_name: str
    comment_text: str
    created_at: datetime
