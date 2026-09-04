# DB access for EvidenceMapping — the per-document clause/control structure written
# by app/tasks/run_gap_analysis.py, one row per (run, document, requirement).
#
# Two read shapes matter downstream, and both are plain queries rather than stored
# aggregates (see ai_iso_plan_27_08_2026.md section 5 — coverage is derived, never
# stored, so it cannot drift from the rows it summarises):
#   - by document: the two-section view (M3)
#   - by requirement: the coverage report behind the readiness gate (M4)

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.ai.source_locator import locate_quote
from app.models.clause import Clause
from app.models.document import Document
from app.models.evidence_mapping import EvidenceMapping


_VERDICT_RANK = {"met": 2, "partial": 1, "unmet": 0}


def _strongest_quote(verdicts: list[dict]) -> str | None:
    quoted = [v for v in verdicts if v.get("quote") and v.get("verdict") in ("met", "partial")]
    if not quoted:
        return None
    quoted.sort(key=lambda v: _VERDICT_RANK.get(v.get("verdict", ""), 0), reverse=True)
    return quoted[0]["quote"]


def record_mappings(
    db: Session,
    *,
    run_id: uuid.UUID,
    document_id: uuid.UUID,
    clauses_by_code: dict[str, Clause],
    evaluations_by_segment: dict[str, list],
    chunks: list[dict] | None,
) -> list[EvidenceMapping]:
    """Persist one document's evaluations for one run, resolving each quote to a
    location as it's written.

    Citations are resolved here rather than on read so they belong to the run: a
    later re-extraction of the document can't silently change what a past
    assessment cited. `locate_quote` returns None when the quote can't be matched,
    which is expected for OCR'd documents — that path produces no positional chunks.

    Caller is responsible for the commit, so one document's rows land atomically
    with the rest of its run.
    """
    rows: list[EvidenceMapping] = []
    for segment, evaluations in evaluations_by_segment.items():
        for evaluation in evaluations:
            clause = clauses_by_code.get(evaluation.requirement_code)
            if clause is None:
                # clause_mapper already drops and logs unknown codes; this is a
                # second guard so a bad code can never become an orphan row.
                continue
            # Each obligation's own quote gets its own location, so the UI can link
            # every line of the reasoning to a passage rather than only the summary.
            verdicts = [
                {
                    "index": v.index,
                    "obligation": (clause.obligations or [])[v.index]
                    if v.index < len(clause.obligations or [])
                    else None,
                    "verdict": v.verdict,
                    "quote": v.quote,
                    "source_location": locate_quote(chunks, v.quote) if v.quote else None,
                }
                for v in evaluation.obligations
            ]
            # The summary quote is derived here rather than read off the evaluation,
            # so this function doesn't depend on normalise_evaluation having run first.
            # It's the strongest verdict's passage — used for the one-line preview and
            # the citation lookup, never as the justification on its own.
            summary_quote = evaluation.rationale or _strongest_quote(verdicts)
            row = EvidenceMapping(
                run_id=run_id,
                document_id=document_id,
                clause_id=clause.id,
                segment=segment,
                coverage_score=evaluation.coverage_score,
                obligation_verdicts=verdicts or None,
                rationale=summary_quote,
                source_location=locate_quote(chunks, summary_quote),
                unmet_guidance_points=evaluation.unmet_guidance_points or None,
            )
            db.add(row)
            rows.append(row)
    return rows


def list_for_document(db: Session, *, document_id: uuid.UUID, run_id: uuid.UUID | None = None) -> list[EvidenceMapping]:
    """One document's mappings, newest run first unless a run is named, ordered by
    requirement so the two-section view renders in catalog order."""
    query = (
        db.query(EvidenceMapping)
        .options(joinedload(EvidenceMapping.clause))
        .join(Clause, EvidenceMapping.clause_id == Clause.id)
        .filter(EvidenceMapping.document_id == document_id)
    )
    if run_id is None:
        run_id = latest_run_id_for_document(db, document_id=document_id)
        if run_id is None:
            return []
    return query.filter(EvidenceMapping.run_id == run_id).order_by(Clause.sort_order).all()


def latest_run_id_for_document(db: Session, *, document_id: uuid.UUID) -> uuid.UUID | None:
    return db.scalar(
        select(EvidenceMapping.run_id)
        .where(EvidenceMapping.document_id == document_id)
        .order_by(EvidenceMapping.created_at.desc())
        .limit(1)
    )


def latest_run_for_organization(
    db: Session, *, organization_id: uuid.UUID, certification_standard: str
) -> tuple[uuid.UUID, datetime] | None:
    """The most recent run under this organization+standard, as (run_id, started_at),
    where started_at is that run's earliest row.

    Needed to tell "analysed and matched nothing" from "never analysed" for a single
    document: a document the LLM read but found nothing in produces no rows at all,
    so there is nothing on the document itself to point at a run. Looking at the
    organization's latest run and comparing timestamps infers it.

    This is an inference, not a record — it can't see a run that produced no rows for
    ANY document. analysis_runs (M4) makes it authoritative by listing the documents
    each run actually read.
    """
    row = db.execute(
        select(EvidenceMapping.run_id, func.min(EvidenceMapping.created_at))
        .join(Document, EvidenceMapping.document_id == Document.id)
        .where(
            Document.organization_id == organization_id,
            Document.certification_standards.contains([certification_standard]),
        )
        .group_by(EvidenceMapping.run_id)
        .order_by(func.min(EvidenceMapping.created_at).desc())
        .limit(1)
    ).first()
    return (row[0], row[1]) if row else None


def contributing_document_counts(db: Session, *, run_id: uuid.UUID) -> dict[uuid.UUID, int]:
    """clause_id -> how many documents contributed evidence for it in this run.

    This is the coverage report: any requirement absent from the result has no
    evidence at all, which is the distinction the readiness gate turns on and the
    one the current findings page cannot make.
    """
    rows = db.execute(
        select(EvidenceMapping.clause_id, func.count(func.distinct(EvidenceMapping.document_id)))
        .where(EvidenceMapping.run_id == run_id)
        .group_by(EvidenceMapping.clause_id)
    ).all()
    return {clause_id: count for clause_id, count in rows}


def delete_run(db: Session, *, run_id: uuid.UUID) -> int:
    """Discard a run's rows — used when a run is superseded or failed part-way.
    Returns the number deleted."""
    deleted = (
        db.query(EvidenceMapping).filter(EvidenceMapping.run_id == run_id).delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def list_for_clause(
    db: Session, *, run_id: uuid.UUID, clause_id: uuid.UUID
) -> list[EvidenceMapping]:
    """Every document's evidence for ONE requirement in one run, strongest first.

    This is what a finding should actually show. The reduce step writes a merged
    narrative onto the finding — prose *about* several documents rather than a quote
    *from* one — so it cannot be located in any document and a multi-document finding
    ends up displaying names and a summary with no verifiable citation. Measured on a
    real 31-document run: 11 of 50 multi-document findings had no resolvable location,
    while 363 of 364 per-document mappings did.

    An auditor confirming a nonconformity has to be able to open the passage. A
    synthesis they cannot verify is not audit evidence, so the per-document rows are
    the evidence and the merged narrative is only a summary of them.
    """
    return (
        db.query(EvidenceMapping)
        .options(joinedload(EvidenceMapping.document))
        .filter(EvidenceMapping.run_id == run_id, EvidenceMapping.clause_id == clause_id)
        .order_by(EvidenceMapping.coverage_score.desc().nullslast())
        .all()
    )
