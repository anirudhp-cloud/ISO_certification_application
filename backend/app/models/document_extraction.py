# DocumentExtraction model — persisted native/OCR'd text+structure, one row per document version.

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True
    )

    extraction_method: Mapped[str] = mapped_column(String(20), nullable=False)  # 'native' | 'ocr'
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Position-tagged chunks — [{"location": "Paragraph 12", "text": "..."}, ...]
    # (see app/extraction/document_extraction.py) — used only to deterministically
    # locate a finding's quoted rationale back to a real page/paragraph/line via
    # app/ai/source_locator.py. extracted_text (above) is still what's sent to
    # the LLM, unchanged; this is purely for citation lookup at read time.
    extracted_chunks: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # delete-orphan because save_extraction() replaces a prior attempt by deleting
    # the extraction row (see app/crud/document_extraction.py). Without the cascade,
    # SQLAlchemy disassociates the image rows by nulling their FK instead of
    # deleting them, which trips document_extracted_images.document_extraction_id's
    # NOT NULL constraint — so re-extracting a document always failed.
    extracted_images: Mapped[list["DocumentExtractedImage"]] = relationship(
        back_populates="document_extraction", cascade="all, delete-orphan", passive_deletes=False
    )
