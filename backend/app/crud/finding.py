# DB access for Finding — one row per (organization, clause), written
# 'unreviewed' by the reduce step (app/ai/aggregator.py) and moved to
# 'reviewed' only when an auditor explicitly Saves it on the Review page.
#
# A finding already mapping_method == 'reviewed' is never silently overwritten
# by upsert_finding_from_mapping/reset_finding_if_auto — an auditor's decision
# survives every later gap-analysis re-run (it can still be cleared, but only
# via an explicit action: review_finding(action="delete"), or a cascading
# document delete/reupload — see app/crud/document.py).

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.grading import propose_grade
from app.models.clause import Clause
from app.models.finding import Finding
from app.models.standard import Standard


def derive_status(coverage_score: float) -> str:
    if coverage_score >= 70:
        return "met"
    if coverage_score >= 30:
        return "partial"
    return "gap"


def list_clause_and_finding_rows(
    db: Session, *, organization_id: uuid.UUID, standard_code: str
) -> list[tuple[Clause, Finding | None]]:
    """Every clause/control for this standard, LEFT JOINed to this organization's
    finding for it (if any) — so a clause with no finding yet still appears,
    read by the API layer as status='not_assessed'."""
    standard = db.query(Standard).filter_by(code=standard_code).one_or_none()
    if standard is None:
        return []

    return (
        db.query(Clause, Finding)
        .outerjoin(Finding, (Finding.clause_id == Clause.id) & (Finding.organization_id == organization_id))
        .filter(Clause.standard_id == standard.id)
        .order_by(Clause.sort_order)
        .all()
    )


def get_finding(db: Session, finding_id: uuid.UUID) -> Finding | None:
    return db.get(Finding, finding_id)


def reset_finding_if_auto(db: Session, *, organization_id: uuid.UUID, clause_id: uuid.UUID) -> None:
    """Called when a clause has zero contributing documents this run — e.g. its only
    backing document was deleted. Drops the finding back to 'not_assessed' (by
    removing the row).

    A reviewed finding is kept, because deleting an auditor's decision silently would
    be worse — but it is now FLAGGED rather than left alone. Previously it was simply
    skipped, so a confirmed finding kept reading 'met' while citing evidence that no
    longer existed: a stale assurance indistinguishable from a live one.
    """
    finding = db.query(Finding).filter_by(organization_id=organization_id, clause_id=clause_id).one_or_none()
    if finding is None:
        return
    if finding.mapping_method != "reviewed":
        db.delete(finding)
        db.commit()
        return

    if not finding.evidence_changed_since_review:
        finding.evidence_changed_since_review = True
        db.commit()


def upsert_finding_from_mapping(
    db: Session,
    *,
    organization_id: uuid.UUID,
    certification_standard: str,
    clause: Clause,
    evidence_document_id: uuid.UUID,
    evidence_document_ids: list[uuid.UUID],
    relevance_score: float,
    coverage_score: float,
    rationale: str,
    unmet_guidance_points: list[str] | None = None,
    analysis_run_id: uuid.UUID | None = None,
) -> Finding:
    """Write (or refresh) the machine's assessment of one requirement.

    Takes the whole `clause` rather than just its id because grading depends on the
    segment: a mandatory clause with weak evidence grades harder than an Annex A
    control, whose severity depends on the risk it treats — and there is no risk
    register here.
    """
    finding = db.query(Finding).filter_by(organization_id=organization_id, clause_id=clause.id).one_or_none()

    if finding is not None and finding.mapping_method == "reviewed":
        # An auditor's decision is never overwritten. But if the evidence behind it
        # has moved, say so instead of leaving the old answer looking current.
        if _evidence_differs(finding, evidence_document_ids, coverage_score):
            finding.evidence_changed_since_review = True
            db.commit()
            db.refresh(finding)
        return finding

    if finding is None:
        finding = Finding(
            organization_id=organization_id,
            clause_id=clause.id,
            certification_standard=certification_standard,
        )
        db.add(finding)

    finding.status = derive_status(coverage_score)
    finding.proposed_grade = propose_grade(
        segment=clause.requirement_type,
        has_evidence=bool(evidence_document_ids),
        coverage_score=coverage_score,
        unmet_guidance_points=unmet_guidance_points,
        is_applicable=finding.is_applicable,
    )
    finding.analysis_run_id = analysis_run_id
    finding.evidence_document_id = evidence_document_id
    finding.evidence_document_ids = evidence_document_ids
    finding.relevance_score = relevance_score
    finding.coverage_score = coverage_score
    finding.rationale = rationale
    finding.unmet_guidance_points = unmet_guidance_points
    finding.mapping_method = "unreviewed"
    finding.evidence_changed_since_review = False

    db.commit()
    db.refresh(finding)
    return finding


def _evidence_differs(finding: Finding, evidence_document_ids: list[uuid.UUID], coverage_score: float) -> bool:
    """Whether a reviewed finding's backing evidence has moved since it was approved —
    a different set of contributing documents, or a materially different coverage
    score from the same ones."""
    previous = set(finding.evidence_document_ids or [])
    if previous != set(evidence_document_ids):
        return True
    if finding.coverage_score is None:
        return coverage_score is not None
    return abs(float(finding.coverage_score) - float(coverage_score)) >= 1.0


def set_applicability(
    db: Session, *, finding_id: uuid.UUID, is_applicable: bool, note: str | None, decided_by: uuid.UUID
) -> Finding:
    """Mark an Annex A control applicable or not.

    Clauses 4-10 are rejected outright: they are mandatory requirements of the
    management system and no organisation may exclude one. Only controls are
    risk-treatment options, and excluding one requires a stated reason —
    without a risk register that justification is the auditor's assertion, not
    something the system derives.
    """
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise ValueError(f"Unknown finding '{finding_id}'")
    if finding.clause.requirement_type != "control":
        raise ValueError(
            f"{finding.clause.code} is a mandatory clause — applicability applies only to Annex A controls"
        )
    if not is_applicable and not (note or "").strip():
        raise ValueError("Excluding a control requires a documented justification")

    finding.is_applicable = is_applicable
    finding.applicability_note = (note or "").strip() or None
    finding.reviewed_by = decided_by
    finding.reviewed_at = func.now()
    finding.proposed_grade = propose_grade(
        segment="control",
        has_evidence=bool(finding.evidence_document_ids),
        coverage_score=float(finding.coverage_score) if finding.coverage_score is not None else None,
        unmet_guidance_points=finding.unmet_guidance_points,
        is_applicable=is_applicable,
    )
    db.commit()
    db.refresh(finding)
    return finding


def review_finding(
    db: Session,
    *,
    finding_id: uuid.UUID,
    action: str,
    reviewed_by: uuid.UUID,
    status: str | None = None,
    relevance_score: float | None = None,
    coverage_score: float | None = None,
    grade: str | None = None,
) -> Finding | None:
    """action == 'save': marks the finding permanent (mapping_method='reviewed'),
    optionally applying the auditor's edited status/scores at the same time —
    the override IS the save, there's no separate confirm-then-override step.
    action == 'delete': removes the row entirely, back to not_assessed — works
    regardless of current mapping_method (an auditor can delete a mistake even
    after having reviewed it)."""
    finding = db.get(Finding, finding_id)
    if finding is None:
        return None

    if action == "delete":
        db.delete(finding)
        db.commit()
        return finding

    # "save"
    if grade is not None:
        # The auditor's decision. Recorded distinctly from proposed_grade so accepting
        # the machine's suggestion is a deliberate act, not an absence of one — and
        # approving a finding clears any stale-evidence flag by definition.
        finding.grade = grade
    finding.evidence_changed_since_review = False
    if relevance_score is not None or coverage_score is not None or status is not None:
        finding.previous_relevance_score = finding.relevance_score
        finding.previous_coverage_score = finding.coverage_score
        if relevance_score is not None:
            finding.relevance_score = relevance_score
        if coverage_score is not None:
            finding.coverage_score = coverage_score
        finding.status = status if status is not None else (
            derive_status(coverage_score) if coverage_score is not None else finding.status
        )
    finding.mapping_method = "reviewed"
    finding.reviewed_by = reviewed_by
    finding.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(finding)
    return finding
