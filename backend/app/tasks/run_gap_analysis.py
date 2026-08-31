# Gap analysis pipeline, in two halves separated by the readiness gate.
#
#   start_run()   maps every active document (two LLM calls each — one per segment),
#                 persists the per-document evidence under a run, records what it
#                 read and what it cost, and STOPS at status='coverage_ready'.
#                 No findings are written.
#
#   accept_run()  the auditor has seen the coverage report and accepted it. Rolls the
#                 evidence up into findings and marks the run accepted.
#
# Why the split: analysis used to run against whatever happened to be uploaded and
# write findings unconditionally, so a requirement nobody had submitted evidence for
# was indistinguishable from one examined and found wanting — the two states that
# matter most in a Stage 1 review. Now coverage is reported first, and accepting on
# incomplete evidence requires a recorded reason.
#
# Execution is still inline rather than through Celery: no Redis is running locally
# (extraction does the same — see tasks/extract_document.py). The gate does not
# depend on that; it needs the run to persist between two requests, which it does
# either way. Switching to `.delay()` is a one-line change once a broker is up.

import logging
import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.ai.aggregator import reduce_clause
from app.ai.clause_mapper import map_document
from app.config import settings
from app.crud.analysis_run import coverage_report, create_run, fail_stale_runs, get_run
from app.crud.document import list_current_documents
from app.crud.document_extraction import get_extraction_for_document
from app.crud.evidence_mapping import record_mappings
from app.models.analysis_run import AnalysisRun
from app.models.clause import Clause
from app.models.evidence_mapping import EvidenceMapping
from app.models.standard import Standard
from app.tasks.celery_app import celery_app

logger = logging.getLogger(f"iso_platform.{__name__}")


class GateNotSatisfied(Exception):
    """Raised when a run with uncovered requirements is accepted without a reason."""


def _load_catalog(db: Session, certification_standard: str) -> list[Clause]:
    standard = db.query(Standard).filter_by(code=certification_standard).one_or_none()
    if standard is None:
        raise ValueError(f"Unknown standard '{certification_standard}'")
    return db.query(Clause).filter(Clause.standard_id == standard.id).order_by(Clause.sort_order).all()


def start_run(
    db: Session,
    *,
    organization_id: uuid.UUID,
    certification_standard: str,
    triggered_by: uuid.UUID,
    tracker=None,
) -> AnalysisRun:
    """Map documents and persist evidence. Leaves the run at 'coverage_ready' —
    findings are written only by accept_run()."""
    clauses = _load_catalog(db, certification_standard)
    # A previous run left at 'running' can only be one whose process died. Close it out
    # first, or it stays the "latest run" forever and hides the last real result.
    abandoned = fail_stale_runs(
        db, organization_id=organization_id, certification_standard=certification_standard
    )
    if abandoned:
        logger.warning("closed out %d interrupted run(s) before starting a new one", abandoned)

    run = create_run(
        db,
        organization_id=organization_id,
        certification_standard=certification_standard,
        triggered_by=triggered_by,
    )
    documents = list_current_documents(
        db, organization_id=organization_id, certification_standard=certification_standard
    )
    # Recorded before mapping so a run that fails part-way still shows what it set
    # out to read.
    run.document_ids = [d.id for d in documents]
    db.commit()

    logger.info(
        "run %s starting: org=%s standard=%s, %d document(s), %d requirement(s)",
        run.id, organization_id, certification_standard, len(documents), len(clauses),
    )

    clauses_by_code = {c.code: c for c in clauses}
    prompt_versions: dict[str, str] = {}
    mapping_rows = 0

    # One try per document, not one around the loop. With the loop inside the try, the
    # first failure abandons every document after it — at 40 documents that's ~80 API
    # calls, and a single rate limit or timeout wasted the whole run and its spend.
    # Isolating each document means one failure costs one document.
    #
    # No fallback: a document that fails produces NOTHING. It is recorded as unread,
    # never as "read and matched nothing", and its absence is never attributed to the
    # organisation's evidence.
    skipped: list[dict] = []
    for document in documents:
        try:
            extraction = get_extraction_for_document(db, document.id)
            segmented = map_document(
                document, extraction, clauses, certification_standard=certification_standard
            )
            prompt_versions.update(segmented.prompt_versions)
            mapping_rows += len(
                record_mappings(
                    db,
                    run_id=run.id,
                    document_id=document.id,
                    clauses_by_code=clauses_by_code,
                    evaluations_by_segment={"clause": segmented.clauses, "control": segmented.controls},
                    chunks=extraction.extracted_chunks if extraction else None,
                )
            )
            # Commit per document, so each one is atomic on its own. Deferring a
            # single commit to the end of the loop looks tidier but breaks the
            # isolation above: record_mappings only calls add(), so a rollback at
            # document 30 would discard documents 1-29's pending rows too — and at
            # 40 documents that turns one failed call back into a lost run.
            db.commit()
        except Exception as exc:
            # Discards only THIS document's half-added rows, because everything
            # before it is already committed.
            db.rollback()
            skipped.append(
                {
                    "document_id": str(document.id),
                    "document_name": document.document_name,
                    "error": f"{type(exc).__name__}: {exc}"[:500],
                }
            )
            logger.exception("run %s: skipping %s", run.id, document.document_name)

    run.skipped_documents = skipped or None
    run.status = "coverage_ready"
    run.completed_at = _now(db)
    run.prompt_version_clause = prompt_versions.get("clause")
    run.prompt_version_control = prompt_versions.get("control")
    run.model_id = settings.llm_deployment
    if tracker is not None:
        run.input_tokens = tracker.prompt_tokens
        run.output_tokens = tracker.completion_tokens
        run.cached_tokens = sum(c.cached_tokens for c in tracker.calls)
        run.cost_usd = tracker.cost_usd
    db.commit()
    db.refresh(run)

    report = coverage_report(db, run=run, clauses=clauses)
    logger.info(
        "run %s coverage_ready in %.1fs: %d evidence mapping(s) from %d of %d document(s); "
        "clauses %d/%d, controls %d/%d, complete=%s",
        run.id,
        (run.completed_at - run.started_at).total_seconds(),
        mapping_rows, len(documents) - len(skipped), len(documents),
        report["clauses"]["covered"], report["clauses"]["total"],
        report["controls"]["covered"], report["controls"]["total"],
        report["is_complete"],
    )
    if skipped:
        logger.warning(
            "run %s skipped %d document(s) — coverage is NOT complete regardless of "
            "requirement counts: %s",
            run.id, len(skipped), ", ".join(d["document_name"] for d in skipped),
        )
    return run


def accept_run(
    db: Session,
    *,
    run_id: uuid.UUID,
    accepted_by: uuid.UUID,
    override_reason: str | None = None,
    tracker=None,
) -> AnalysisRun:
    """Roll a coverage_ready run's evidence up into findings.

    Refuses when requirements have no evidence and no reason was given — that's the
    gate. With a reason, it proceeds and records it, so "we knowingly assessed on
    incomplete evidence" is never indistinguishable from a complete run.
    """
    run = get_run(db, run_id)
    if run is None:
        raise ValueError(f"Unknown run '{run_id}'")
    if run.status == "accepted":
        return run  # idempotent: a double-click must not re-write findings
    if run.status != "coverage_ready":
        raise ValueError(f"Run {run_id} is '{run.status}' — only a coverage_ready run can be accepted")

    clauses = _load_catalog(db, run.certification_standard)
    report = coverage_report(db, run=run, clauses=clauses)
    if not report["is_complete"] and not (override_reason or "").strip():
        missing = report["clauses"]["missing_codes"] + report["controls"]["missing_codes"]
        raise GateNotSatisfied(
            f"{len(missing)} requirement(s) have no evidence. Supply more documents, or accept "
            f"anyway with a stated reason."
        )

    # Group this run's persisted evidence back by requirement for the rollup, so the
    # findings are derived from what was stored rather than from in-memory state.
    rows = (
        db.query(EvidenceMapping)
        .filter(EvidenceMapping.run_id == run.id)
        .all()
    )
    contributions_by_clause = defaultdict(list)
    for row in rows:
        contributions_by_clause[row.clause_id].append((row.document, row))

    for clause in clauses:
        reduce_clause(
            db,
            organization_id=run.organization_id,
            certification_standard=run.certification_standard,
            clause=clause,
            contributions=contributions_by_clause.get(clause.id, []),
            analysis_run_id=run.id,
        )

    # The reduce calls cost money too — one per requirement with 2+ contributing
    # documents, so at 40 documents that's up to 70 more calls. Without this they were
    # logged per call but never added to the run, so run.cost_usd understated the true
    # cost of an Analyze by the whole accept phase.
    if tracker is not None:
        run.input_tokens = (run.input_tokens or 0) + tracker.prompt_tokens
        run.output_tokens = (run.output_tokens or 0) + tracker.completion_tokens
        run.cached_tokens = (run.cached_tokens or 0) + sum(c.cached_tokens for c in tracker.calls)
        run.cost_usd = float(run.cost_usd or 0) + tracker.cost_usd

    run.status = "accepted"
    run.gate_accepted_by = accepted_by
    run.gate_accepted_at = _now(db)
    run.gate_override_reason = (override_reason or "").strip() or None
    db.commit()
    db.refresh(run)

    logger.info(
        "run %s accepted by %s%s",
        run.id, accepted_by,
        f" (override: {run.gate_override_reason})" if run.gate_override_reason else "",
    )
    return run


def _now(db: Session):
    """Database wall clock, so run timestamps come from one source rather than mixing
    the app server's time with server_default=now().

    clock_timestamp(), NOT now(): PostgreSQL's now() returns the time the current
    TRANSACTION started, so it reported a 27-second run as having taken 0.05s — the
    field meant to tell you how long a run took was measuring nothing.
    clock_timestamp() is the real clock and is unaffected by transaction boundaries.
    """
    from sqlalchemy import func, select

    return db.scalar(select(func.clock_timestamp()))


@celery_app.task(name="run_gap_analysis")
def run_gap_analysis_task(organization_id: str, certification_standard: str, triggered_by: str) -> None:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        start_run(
            db,
            organization_id=uuid.UUID(organization_id),
            certification_standard=certification_standard,
            triggered_by=uuid.UUID(triggered_by),
        )
    finally:
        db.close()
