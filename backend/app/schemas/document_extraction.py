# Pydantic schemas for reading back a document's extraction result.

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentExtractedImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_number: int | None
    ocr_text: str | None


class DocumentExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    extraction_method: str
    extracted_text: str
    created_at: datetime
    extracted_images: list[DocumentExtractedImageRead]
