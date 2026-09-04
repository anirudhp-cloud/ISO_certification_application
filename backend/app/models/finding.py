# Finding model — one row per (organization, standard, clause): status, evidence, auditor review state.
#
# coverage_score is COMPUTED from obligation verdicts (app/ai/scoring.py), never
# supplied by the model — and obligation_rollup carries the reasoning behind it.
# The model used to return coverage and relevance percentages directly; across 1,057
# real mappings only 30 distinct values appeared out of 101 and 98% were multiples of
# 5, so neither number could be accounted for. Both are gone as model output.

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

STATUS_VALUES = ("not_assessed", "met", "partial", "gap", "not_applicable")
# Two states only: "unreviewed" (written by the LLM pipeline, pending on the
# Review page) and "reviewed" (an auditor explicitly Saved it — permanent).
MAPPING_METHOD_VALUES = ("unreviewed", "reviewed")
# What a certification body actually issues, replacing the invented 70/30
# met/partial/gap buckets. A major NC blocks certification; an OFI does not —
# a distinction a coverage percentage cannot express.
GRADE_VALUES = ("conforming", "ofi", "minor_nc", "major_nc", "not_applicable")


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("organization_id", "clause_id", name="uq_findings_organization_clause"),
        CheckConstraint(f"status IN {STATUS_VALUES}", name="ck_findings_status"),
        CheckConstraint(f"mapping_method IN {MAPPING_METHOD_VALUES}", name="ck_findings_mapping_method"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    clause_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)
    # Denormalized from clauses -> standards, same pattern as documents.certification_standard,
    # so "findings for this org + standard" doesn't need a join.
    certification_standard: Mapped[str] = mapped_column(String(20), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_assessed")

    evidence_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True
    )
    # Every document that contributed to the current combined result (see
    # app/ai/aggregator.py) — evidence_document_id above stays the single
    # primary/highest-scoring one, for simple "open the source" click-through.
    evidence_document_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    coverage_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The requirement-level reasoning, computed by app/ai/rollup.py: every obligation,
    # the strongest verdict any document achieved for it, which documents supplied
    # that, and which obligations no document satisfies at all. This is what the UI
    # renders instead of a prose summary — the last item is the audit question.
    obligation_rollup: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Subset of clause.implementation_guidance (Annex B) the LLM judged NOT
    # satisfied by the evidence — drives the Gap Analysis checklist. Met points
    # are derived at read time (full list minus this), not stored separately.
    unmet_guidance_points: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    mapping_method: Mapped[str] = mapped_column(String(20), nullable=False, default="unreviewed")

    # Which run produced the current machine suggestion, so a finding can be traced
    # back to the documents, prompt and model behind it.
    analysis_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="SET NULL"), nullable=True
    )

    # Annex A controls only — NULL for all 32 clauses, which can never be excluded.
    # A false value requires applicability_note: an exclusion without a stated reason
    # is not one an auditor can defend.
    is_applicable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    applicability_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # proposed_grade is the machine's suggestion; grade is the auditor's decision.
    # Kept apart so accepting a suggestion is a recorded act, not an absence of one.
    proposed_grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Raised when a reviewed finding's evidence changed underneath it. Previously
    # both write paths simply skipped reviewed rows, so a confirmed finding kept
    # citing evidence that had been deleted or replaced.
    evidence_changed_since_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    previous_coverage_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    clause: Mapped["Clause"] = relationship()
