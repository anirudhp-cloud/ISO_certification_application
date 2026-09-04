# DB access for AnalysisRun, plus the coverage report the readiness gate turns on.

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.clause import Clause
from app.models.evidence_mapping import EvidenceMapping


def create_run(
    db: Session, *, organization_id: uuid.UUID, certification_standard: str, triggered_by: uuid.UUID
) -> AnalysisRun:
    run = AnalysisRun(
        organization_id=organization_id,
        certification_standard=certification_standard,
        triggered_by=triggered_by,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: uuid.UUID) -> AnalysisRun | None:
    return db.get(AnalysisRun, run_id)


# A 'running' run is only stale once it has been running longer than any real run
# plausibly takes. Without this threshold, a request that merely CHECKS on progress
# (the pending-run banner polling GET /runs/latest) marked the in-flight run failed:
# a real 44-document run took 13 minutes, and the poll landed in the middle of it, so
# a run that went on to finish perfectly well carried "Interrupted — the server
# stopped before this run finished" for the rest of its life.
STALE_RUN_AFTER_MINUTES = 120


def fail_stale_runs(db: Session, *, organization_id: uuid.UUID, certification_standard: str) -> int:
    """Mark a run abandoned mid-flight as failed, so it stops masking the last real
    result.

    Execution is inline in the request, so a run stuck at 'running' usually means the
    process that owned it went away. But a run legitimately sits at 'running' while it
    executes, and this is called from a read endpoint — so only runs older than
    STALE_RUN_AFTER_MINUTES are touched. Returns how many were closed out.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STALE_RUN_AFTER_MINUTES)
    stale = (
        db.query(AnalysisRun)
        .filter_by(organization_id=organization_id, certification_standard=certification_standard, status="running")
        .filter(AnalysisRun.started_at < cutoff)
        .all()
    )
    for run in stale:
        run.status = "failed"
        run.error_message = (
            "Interrupted — the server stopped before this run finished. "
            "Its partial evidence is not used; start a new analysis."
        )
    if stale:
        db.commit()
    return len(stale)


def latest_run(db: Session, *, organization_id: uuid.UUID, certification_standard: str) -> AnalysisRun | None:
    return (
        db.query(AnalysisRun)
        .filter_by(organization_id=organization_id, certification_standard=certification_standard)
        .order_by(AnalysisRun.started_at.desc())
        .first()
    )


def latest_actionable_run(
    db: Session, *, organization_id: uuid.UUID, certification_standard: str
) -> AnalysisRun | None:
    """The run the auditor actually needs to see.

    Strictly "the most recent run" is the wrong answer. A failed attempt started after
    a successful one would hide it — and that is not hypothetical: a 31-document run
    finished with 364 evidence mappings, then a second run was started and killed with
    the server, and the newer failure buried the older result completely.

    So prefer the most recent run whose results can still be acted on
    (coverage_ready), and fall back to the most recent run of any status only when
    there is nothing waiting. A later failure is reported separately by the caller
    rather than replacing the usable result.
    """
    ready = (
        db.query(AnalysisRun)
        .filter_by(
            organization_id=organization_id,
            certification_standard=certification_standard,
            status="coverage_ready",
        )
        .order_by(AnalysisRun.started_at.desc())
        .first()
    )
    if ready is not None:
        return ready
    return latest_run(db, organization_id=organization_id, certification_standard=certification_standard)


def skipped_document_ids(run: AnalysisRun | None) -> set[uuid.UUID]:
    if run is None or not run.skipped_documents:
        return set()
    return {uuid.UUID(entry["document_id"]) for entry in run.skipped_documents}


def read_this_document(run: AnalysisRun | None, document_id: uuid.UUID) -> bool:
    """Whether a run actually read this document.

    The authoritative answer to the question M3 could only infer: a document the LLM
    found nothing in produces no evidence_mappings rows, so without the run's own
    document list there is nothing to distinguish "read and matched nothing" from
    "never analysed".

    A skipped document counts as NOT read. It was in scope and the attempt failed, so
    claiming it was read and matched nothing would assert something that never
    happened — the report would blame the organisation for evidence nobody looked at.
    """
    if run is None or not run.document_ids or document_id not in run.document_ids:
        return False
    return document_id not in skipped_document_ids(run)


def coverage_report(db: Session, *, run: AnalysisRun, clauses: list[Clause]) -> dict:
    """Per-segment coverage for one run: which requirements have evidence and which
    have none.

    Derived by query rather than stored, so it can never disagree with the rows it
    summarises. Reported per segment because the two mean different things — a clause
    with no evidence is a hard gap, a control with none might simply be inapplicable.
    """
    covered_ids = {
        clause_id
        for (clause_id,) in db.query(EvidenceMapping.clause_id).filter(EvidenceMapping.run_id == run.id).distinct()
    }

    segments: dict[str, dict] = {}
    for segment in ("clause", "control"):
        in_segment = [c for c in clauses if c.requirement_type == segment]
        covered = [c for c in in_segment if c.id in covered_ids]
        missing = [c for c in in_segment if c.id not in covered_ids]
        segments[segment] = {
            "segment": segment,
            "total": len(in_segment),
            "covered": len(covered),
            "missing_codes": [c.code for c in missing],
            "missing_titles": {c.code: c.title for c in missing},
        }

    skipped = list(run.skipped_documents or [])

    # A skipped document makes coverage UNKNOWABLE, not merely lower: whatever it
    # contained was never read, so no requirement count can be trusted to mean what it
    # says. Reporting complete here would let the gate wave through a run that never
    # opened the risk register.
    fully_covered = not (segments["clause"]["missing_codes"] or segments["control"]["missing_codes"])

    return {
        "run_id": run.id,
        "status": run.status,
        "is_complete": fully_covered and not skipped,
        "skipped_documents": skipped,
        "documents_read": len(run.document_ids or []) - len(skipped),
        "documents_total": len(run.document_ids or []),
        "clauses": segments["clause"],
        "controls": segments["control"],
    }
