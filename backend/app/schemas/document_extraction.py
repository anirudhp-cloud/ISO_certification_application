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


class DocumentPreviewInfoRead(BaseModel):
    """Whether the document can be shown in the browser, and where the quote sits.

    Every format is served as a PDF (LibreOffice converts docx/pptx/xlsx), so the
    viewer has one code path and shows the real document rather than a re-rendering of
    its text. `page` is where the cited passage was found and highlighted.
    """

    document_id: uuid.UUID
    document_name: str
    file_name: str
    version_number: int
    available: bool
    # Why no preview, or why the quote could not be highlighted. Shown to the auditor
    # rather than silently opening page 1.
    reason: str | None = None
    page: int | None = None
    preview_url: str | None = None
    # Always present — the original file, whatever happens with the preview.
    file_url: str
