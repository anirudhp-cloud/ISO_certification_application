# Document model — versioned, soft-deleted, keyed by organization_id + certification_standards.

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    # A document can count toward more than one standard at once (e.g. one
    # combined Quality & AI Manual satisfies both ISO 42001 and ISO 9001) —
    # an array rather than a join table, matching evidence_document_ids/
    # unmet_guidance_points/implementation_guidance elsewhere in this schema.
    certification_standards: Mapped[list[str]] = mapped_column(ARRAY(String(20)), nullable=False)

    # versioning
    document_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True
    )

    # descriptive metadata (fixed at creation, carried forward across versions)
    document_name: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # how this version was submitted — 'upload' | 'share_path' | 'zip' (frontend's 3 ingestion tabs)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # file — for 'upload'/'zip' this is a real stored file; for 'share_path' storage_path
    # holds the shared/network path itself and no bytes are ever transferred or stored.
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    # who created the document (the original submission — stays the same across versions)
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # who produced *this* version, and when
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    review_comments: Mapped[list["DocumentReviewComment"]] = relationship(back_populates="document")

    # Disambiguated because there are 3 separate FKs to users.id on this table.
    submitted_by_user: Mapped["User"] = relationship(foreign_keys=[submitted_by])
    updated_by_user: Mapped["User | None"] = relationship(foreign_keys=[updated_by])

    # Convenience for API responses — lets the frontend show a name without
    # ever needing to fetch/cache the full user list (which would otherwise
    # expose every user's email, undesirable now that accounts are real).
    @property
    def submitted_by_name(self) -> str:
        return self.submitted_by_user.name

    @property
    def updated_by_name(self) -> str | None:
        return self.updated_by_user.name if self.updated_by_user else None
