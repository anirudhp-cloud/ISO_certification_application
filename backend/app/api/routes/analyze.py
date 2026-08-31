# Analyze — now two steps with the readiness gate between them.
#
#   POST /organizations/{id}/standards/{std}/analyze   maps documents, persists
#       evidence, reports coverage. Writes NO findings.
#   GET  /runs/{run_id}                                status + coverage report
#   POST /runs/{run_id}/accept                         writes the findings
#
# Analysis used to run against whatever happened to be uploaded and write findings
# unconditionally, so a requirement nobody had submitted evidence for was
# indistinguishable from one examined and found wanting. Now the auditor sees what is
# missing before anything is graded, and accepting on incomplete evidence requires a
# stated reason that is recorded on the run.
#
# An unauthenticated single-document test endpoint (POST /api/analyze, taking ad-hoc
# pasted-in text) used to live here. It was removed in M1: nothing called it, it
# required no login, and it spent model tokens on arbitrary input.

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.cost_tracker import tracking
from app.api.routes.findings import load_findings, summarize_findings
from app.crud.analysis_run import (
    coverage_report,
    fail_stale_runs,
    get_run,
    latest_actionable_run,
)
from app.deps import get_db, require_auditor, require_auditor_org_access, require_run_access
from app.models.clause import Clause
from app.models.standard import Standard
from app.models.user import User
from app.schemas.analysis_run import AnalysisRunRead, RunAcceptRequest
from app.schemas.finding import FindingsReportRead
from app.tasks.run_gap_analysis import GateNotSatisfied, accept_run, start_run

logger = logging.getLogger(f"iso_platform.{__name__}")
router = APIRouter()


def _catalog(db: Session, certification_standard: str) -> list[Clause]:
    standard = db.query(Standard).filter_by(code=certification_standard).one_or_none()
    if standard is None:
        return []
    return db.query(Clause).filter(Clause.standard_id == standard.id).order_by(Clause.sort_order).all()


def _run_response(db: Session, run) -> AnalysisRunRead:
    report = coverage_report(db, run=run, clauses=_catalog(db, run.certification_standard))
    return AnalysisRunRead(
        id=run.id,
        organization_id=run.organization_id,
        certification_standard=run.certification_standard,
        status=run.status,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        document_count=len(run.document_ids or []),
        prompt_version_clause=run.prompt_version_clause,
        prompt_version_control=run.prompt_version_control,
        model_id=run.model_id,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        cached_tokens=run.cached_tokens,
        cost_usd=float(run.cost_usd) if run.cost_usd is not None else None,
        gate_accepted_at=run.gate_accepted_at,
        gate_override_reason=run.gate_override_reason,
        skipped_documents=report["skipped_documents"],
        documents_read=report["documents_read"],
        is_complete=report["is_complete"],
        clauses=report["clauses"],
        controls=report["controls"],
    )


@router.post(
    "/organizations/{organization_id}/standards/{standard}/analyze", response_model=AnalysisRunRead
)
def start_analysis(
    organization_id: uuid.UUID,
    standard: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor_org_access),
) -> AnalysisRunRead:
    """Step 1: map every active document and report coverage. No findings written."""
    logger.info("analyze triggered by %s for org %s, standard %s", current_user.id, organization_id, standard)

    try:
        with tracking() as tracker:
            run = start_run(
                db,
                organization_id=organization_id,
                certification_standard=standard,
                triggered_by=current_user.id,
                tracker=tracker,
            )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    logger.info(
        "run %s: %d LLM call(s), %d tokens, $%.6f",
        run.id, tracker.call_count, tracker.total_tokens, tracker.cost_usd,
    )
    return _run_response(db, run)


@router.get(
    "/organizations/{organization_id}/standards/{standard}/runs/latest",
    response_model=AnalysisRunRead | None,
)
def get_latest_run(
    organization_id: uuid.UUID,
    standard: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor_org_access),
) -> AnalysisRunRead | None:
    """The most recent run for this organization+standard, or null if none.

    Without this the UI could only ever see a run through the response of the POST
    that started it — and that POST takes minutes (17 for a real 31-document set). If
    the browser gave up, navigated away, or the page was reloaded, a completed run
    became invisible: 364 evidence mappings sitting in the database with no route to
    them, and the only apparent recourse was to pay for another run.

    Returns the most recent run with results still waiting for the gate, falling back
    to the most recent run of any status. Deliberately not "strictly the newest": a
    failed attempt started after a successful one would otherwise bury it — which is
    exactly what happened when a completed 31-document run was followed by a second
    run that died with the server.
    """
    # A run left at 'running' by a stopped process would otherwise mask the last real
    # result forever, so close those out first.
    fail_stale_runs(db, organization_id=organization_id, certification_standard=standard)

    run = latest_actionable_run(
        db, organization_id=organization_id, certification_standard=standard
    )
    return _run_response(db, run) if run is not None else None


@router.get("/runs/{run_id}", response_model=AnalysisRunRead)
def get_analysis_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_run_access),
) -> AnalysisRunRead:
    run = get_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _run_response(db, run)


@router.post("/runs/{run_id}/accept", response_model=FindingsReportRead)
def accept_analysis_run(
    run_id: uuid.UUID,
    payload: RunAcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_run_access),
    _auditor: User = Depends(require_auditor),
) -> FindingsReportRead:
    """Step 2: the gate. Rolls the run's evidence up into findings.

    Returns 409 — not 400 — when requirements have no evidence and no override reason
    was given: the request was well-formed, the state just isn't ready for it, and the
    client's move is to supply more documents or an explicit reason.
    """
    try:
        with tracking() as tracker:
            run = accept_run(
                db,
                run_id=run_id,
                accepted_by=current_user.id,
                override_reason=payload.override_reason,
                tracker=tracker,
            )
    except GateNotSatisfied as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    logger.info(
        "run %s accept: %d reduce call(s), %d tokens, $%.6f — run total now $%s",
        run.id, tracker.call_count, tracker.total_tokens, tracker.cost_usd, run.cost_usd,
    )

    findings = load_findings(db, run.organization_id, run.certification_standard)
    return FindingsReportRead(
        findings=findings,
        overall=summarize_findings(findings),
        controls=summarize_findings(findings, requirement_type="control"),
        clauses=summarize_findings(findings, requirement_type="clause"),
    )
