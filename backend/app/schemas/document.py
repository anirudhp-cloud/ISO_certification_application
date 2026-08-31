# Pydantic schemas for Document — upload, share-path, zip-result, read.

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DocumentShareReference(BaseModel):
    """The 'share_path' upload variant — no file bytes transferred, just a reference."""

    document_name: str
    document_type: str
    file_name: str
    share_path: str
    # Standards beyond the one implied by the URL this is posted to (e.g. also
    # tag this upload for ISO 9001 when uploading under the ISO 42001 view).
    additional_standards: list[str] = []


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    certification_standards: list[str]
    document_group_id: uuid.UUID
    version_number: int
    is_current: bool
    document_name: str
    document_type: str
    source_type: str
    file_name: str
    submitted_by: uuid.UUID
    submitted_by_name: str
    submitted_at: datetime
    updated_by: uuid.UUID | None
    updated_by_name: str | None
    updated_at: datetime


class SkippedZipEntry(BaseModel):
    """An archive entry that did not become a document, and why.

    Reported rather than dropped: an unreadable file that silently became a
    zero-text document would sit in the list looking like real evidence, contribute
    nothing, and make its requirements read as uncovered by the organisation.
    """

    path: str  # full path inside the archive
    reason: str


class ZipUploadResult(BaseModel):
    created: list[DocumentRead]
    skipped: list[SkippedZipEntry] = []
    # Document names that already existed under this organization+standard. Uploading
    # the same archive twice would otherwise double the document set — and the cost of
    # the next Analyze — with no warning.
    duplicate_names: list[str] = []


class DocumentVersionRead(DocumentRead):
    previous_version_id: uuid.UUID | None


SourceType = Literal["upload", "share_path", "zip"]
