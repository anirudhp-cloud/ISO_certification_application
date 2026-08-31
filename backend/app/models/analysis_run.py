# AnalysisRun — one Analyze, as a record rather than an event that leaves no trace.
#
# Two things this makes possible that weren't before:
#
#   1. Provenance. Findings used to be mutated in place with nothing recording when
#      analysis ran, which document versions it read, or which prompt and model
#      produced the result. On a platform whose output is audit evidence, an
#      assessment you can't reconstruct is one you can't defend to a certification
#      body. Runs are insert-only; a re-analysis is a new row, never an update.
#
#   2. The readiness gate. Analyze and "write the findings" are now two requests, so
#      the run has to persist between them: the first maps documents and reports
#      coverage, the auditor reviews it, the second accepts. `gate_override_reason`
#      records the case where they accepted anyway.
#
# document_ids is the reason this table matters for the per-document view too: a
# document the LLM read but found nothing in produces no evidence_mappings rows, so
# without a list of what each run read, "analysed and matched nothing" can only be
# inferred (see crud/evidence_mapping.latest_run_for_organization). With it, that
# question has an answer.

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# running        — mapping in progress
# coverage_ready — mapped and persisted; coverage reported, findings NOT yet written
# accepted       — the auditor accepted the coverage; findings written
# failed         — aborted; error_message says why
STATUS_VALUES = ("running", "coverage_ready", "accepted", "failed")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        CheckConstraint(f"status IN {STATUS_VALUES}", name="ck_analysis_runs_status"),
        Index("ix_analysis_runs_org_standard", "organization_id", "certification_standard", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    certification_standard: Mapped[str] = mapped_column(String(20), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    triggered_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # The exact document versions this run set out to read — not "the org's current
    # documents", which drifts as soon as anyone uploads.
    document_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)

    # Documents this run could NOT read, with the reason:
    # [{"document_id": ..., "document_name": ..., "error": ...}, ...]
    #
    # Recorded so an absent result never becomes an asserted one. Without it, a
    # document that failed mid-run is indistinguishable from one that was read and
    # matched nothing — and the coverage report would blame the organisation for
    # evidence that was never actually looked at. Anything listed here is excluded
    # from read_this_document() and forces the run's coverage to report incomplete.
    skipped_documents: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # What produced the results, so runs under different prompt revisions or models
    # stay distinguishable instead of sitting side by side looking identical.
    prompt_version_clause: Mapped[str | None] = mapped_column(String(60), nullable=True)
    prompt_version_control: Mapped[str | None] = mapped_column(String(60), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(80), nullable=True)

    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cached_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)

    # Set when the auditor accepts the coverage report and findings are written.
    # gate_override_reason is required only when they accepted despite requirements
    # having no evidence — so "we knowingly assessed on incomplete evidence" is
    # recorded rather than indistinguishable from a complete run.
    gate_accepted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    gate_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gate_override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
