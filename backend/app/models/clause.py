# Clause/control model — the fixed catalog a document is evaluated against, per standard.
#
# Deliberately one table for both ISO clauses (4-10) and Annex A controls
# (requirement_type discriminates) rather than two — the mapping/scoring
# mechanics are identical for both, and a document is evaluated against
# only its own standard's rows (see the framework-isolation rule in
# ISO42001_Certification_Platform.md's Gap Analysis section).

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Clause(Base):
    __tablename__ = "clauses"
    __table_args__ = (UniqueConstraint("standard_id", "code", name="uq_clauses_standard_code"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    standard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("standards.id"), nullable=False)

    requirement_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'clause' | 'control'
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    # Explicit display order, populated by app/seed.py from the seed file's own
    # sequence. Needed because ordering by (category, code) sorted them as text —
    # "10 Improvement" ahead of "4 Context of the organization".
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_requirements: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    # Annex B "Implementation guidance" bullets for this Annex A control (the
    # standard's "how", vs. description's one-line Annex A "what") — only
    # populated for requirement_type == "control" rows; NULL for clauses 4-10,
    # which have no Annex B counterpart.
    implementation_guidance: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    standard: Mapped["Standard"] = relationship(back_populates="clauses")
