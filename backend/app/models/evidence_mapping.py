# EvidenceMapping — one row per (run, document, requirement): the per-document
# clause/control structure produced by the two map passes.
#
# This is the record that didn't exist before M2. The map step's results used to
# live in a local dict in run_gap_analysis, get reduced straight into Finding rows,
# and then be discarded — so "which clauses and controls does THIS document
# satisfy?" was unanswerable, and nothing recorded what a past run actually saw.
#
# Grain matters: findings are one row per (organization, requirement) — a rollup
# across every contributing document. These are one row per (document, requirement),
# which is what the document view, the coverage report and the audit trail all need.
# Findings become a derived view over these rows rather than the primary record.

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
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

SEGMENT_VALUES = ("clause", "control")


class EvidenceMapping(Base):
    __tablename__ = "evidence_mappings"
    __table_args__ = (
        UniqueConstraint("run_id", "document_id", "clause_id", name="uq_evidence_mappings_run_doc_clause"),
        CheckConstraint(f"segment IN {SEGMENT_VALUES}", name="ck_evidence_mappings_segment"),
        Index("ix_evidence_mappings_run_segment", "run_id", "segment"),
        Index("ix_evidence_mappings_document", "document_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Plain UUID, not a foreign key, until analysis_runs exists at M4 — the run is
    # already a real grouping (all rows written by one Analyze) and making it an FK
    # later is an additive migration.
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # The specific document *version* that supplied this evidence, so a citation
    # stays attached to the text it was actually found in.
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    clause_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)

    # Denormalized from clauses.requirement_type so the document view and the
    # coverage report can split by segment without joining.
    segment: Mapped[str] = mapped_column(String(10), nullable=False)

    # COMPUTED from obligation_verdicts below, never supplied by the model. Retained
    # as a number only for ordering and for the grade rule; the UI shows "n of m
    # satisfied" instead, because with 3 obligations the only honest values are
    # 0/1/2/3 of 3 and a percentage implies a granularity that does not exist.
    coverage_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # [{"index": 0, "verdict": "met"|"partial"|"unmet", "quote": ..., "source_location": ...}]
    # The assessment itself: one answer per obligation in clauses.obligations, each
    # with the passage that justifies it. This is what the UI renders as the reasoning
    # — there is no separate prose explanation, because prose written after a guessed
    # number is decoration on the guess.
    obligation_verdicts: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # The LLM's verbatim quote from the document — required by both map prompts,
    # and the input to the citation lookup below.
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Where that quote sits, e.g. 'Section "7. Policy Review", paragraph 1'. Resolved
    # by app/ai/source_locator.py at WRITE time rather than on every read: the
    # citation then belongs to the run, and can't silently change if the document is
    # re-extracted afterwards. NULL when the quote couldn't be matched — which
    # happens for OCR'd documents, since that path yields no positional chunks.
    source_location: Mapped[str | None] = mapped_column(String(160), nullable=True)

    # Annex B points the LLM judged unsatisfied. Always empty for the clause
    # segment: clauses have no Annex B.
    unmet_guidance_points: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clause: Mapped["Clause"] = relationship()
    document: Mapped["Document"] = relationship()
