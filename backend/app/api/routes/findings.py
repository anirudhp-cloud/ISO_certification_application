# Findings endpoints — list (all 70 requirements, joined against whatever this
# organization has for each), auditor confirm/override, and a readiness report.

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.grading import GRADE_LABELS, evidence_state, propose_grade
from app.ai.source_locator import locate_quote
from app.crud.document import get_documents_by_ids
from app.crud.document_extraction import get_extractions_for_documents
from app.crud.evidence_mapping import list_for_clause
from app.crud.finding import (
    get_finding,
    list_clause_and_finding_rows,
    review_finding,
    set_applicability,
)
from app.deps import get_current_user, get_db, require_auditor, require_auditor_org_access
from app.models.clause import Clause
from app.models.finding import Finding
from app.models.user import User
from app.schemas.evidence_mapping import FindingEvidenceItem, FindingEvidenceRead
from app.schemas.finding import (
    ApplicabilityRequest,
    EvidenceDocumentRef,
    FindingRead,
    FindingReviewRequest,
    FindingsReportRead,
    FindingsSummary,
    build_guidance_checklist,
)

logger = logging.getLogger(f"iso_platform.{__name__}")
router = APIRouter()


def _compute_source_location(finding: Finding | None, extractions_by_doc_id: dict) -> str | None:
    """Tries the primary evidence document first, then every other contributing
    document, until the rationale's quoted passage is actually found — a
    combined multi-document rationale can quote any of them."""
    if finding is None or not finding.rationale:
        return None
    candidate_ids = [finding.evidence_document_id, *(finding.evidence_document_ids or [])]
    seen = set()
    for doc_id in candidate_ids:
        if doc_id is None or doc_id in seen:
            continue
        seen.add(doc_id)
        extraction = extractions_by_doc_id.get(doc_id)
        if extraction is None:
            continue
        location = locate_quote(extraction.extracted_chunks, finding.rationale)
        if location is not None:
            return location
    return None


def _build_finding_read(
    clause: Clause, finding: Finding | None, documents_by_id: dict, extractions_by_doc_id: dict
) -> FindingRead:
    evidence_ids = (finding.evidence_document_ids if finding else None) or []
    evidence = [
        EvidenceDocumentRef(document_id=doc_id, document_name=documents_by_id[doc_id].document_name)
        for doc_id in evidence_ids
        if doc_id in documents_by_id
    ]
    coverage = (
        float(finding.coverage_score) if finding is not None and finding.coverage_score is not None else None
    )
    proposed = (
        finding.proposed_grade
        if finding is not None and finding.proposed_grade
        else propose_grade(
            segment=clause.requirement_type,
            has_evidence=bool(evidence_ids),
            coverage_score=coverage,
            unmet_guidance_points=finding.unmet_guidance_points if finding else None,
            is_applicable=finding.is_applicable if finding else None,
        )
    )

    return FindingRead(
        clause_id=clause.id,
        requirement_type=clause.requirement_type,
        code=clause.code,
        category=clause.category,
        title=clause.title,
        finding_id=finding.id if finding else None,
        status=finding.status if finding else "not_assessed",
        relevance_score=finding.relevance_score if finding else None,
        coverage_score=finding.coverage_score if finding else None,
        rationale=finding.rationale if finding else None,
        source_location=_compute_source_location(finding, extractions_by_doc_id),
        evidence=evidence,
        mapping_method=finding.mapping_method if finding else None,
        reviewed_by=finding.reviewed_by if finding else None,
        reviewed_at=finding.reviewed_at if finding else None,
        guidance_checklist=build_guidance_checklist(
            clause.implementation_guidance, finding.unmet_guidance_points if finding else None
        ),
        # Derived rather than stored, so it can't drift from the evidence it
        # describes. This is the distinction status could never make: nothing
        # submitted yet vs submitted and inadequate.
        evidence_state=evidence_state(has_evidence=bool(evidence_ids), coverage_score=coverage),
        # A requirement with no finding row still has a grade position: nothing was
        # submitted for it, which in a Stage 1 documentation review is a
        # nonconformity, not an absence of information. Derived here rather than
        # written as 70-odd "we found nothing" rows, so deleting a document still
        # cleanly drops its finding.
        proposed_grade=proposed,
        grade=finding.grade if finding else None,
        grade_label=GRADE_LABELS.get((finding.grade if finding else None) or proposed),
        is_applicable=finding.is_applicable if finding else None,
        applicability_note=finding.applicability_note if finding else None,
        evidence_changed_since_review=finding.evidence_changed_since_review if finding else False,
        analysis_run_id=finding.analysis_run_id if finding else None,
    )


def load_findings(db: Session, organization_id: uuid.UUID, standard: str) -> list[FindingRead]:
    rows = list_clause_and_finding_rows(db, organization_id=organization_id, standard_code=standard)

    all_evidence_ids = {
        doc_id
        for _, finding in rows
        if finding is not None and finding.evidence_document_ids
        for doc_id in finding.evidence_document_ids
    }
    documents_by_id = get_documents_by_ids(db, list(all_evidence_ids))
    extractions_by_doc_id = get_extractions_for_documents(db, list(all_evidence_ids))

    return [_build_finding_read(clause, finding, documents_by_id, extractions_by_doc_id) for clause, finding in rows]


def summarize_findings(findings: list[FindingRead], *, requirement_type: str | None = None) -> FindingsSummary:
    if requirement_type is not None:
        findings = [f for f in findings if f.requirement_type == requirement_type]

    counts = {"met": 0, "partial": 0, "gap": 0, "not_assessed": 0}
    grades = {"conforming": 0, "ofi": 0, "minor_nc": 0, "major_nc": 0, "not_applicable": 0}
    for f in findings:
        counts[f.status if f.status in counts else "not_assessed"] += 1
        # The auditor's decision wins over the machine's suggestion; a requirement
        # with neither simply isn't graded yet and is counted in neither bucket.
        effective = f.grade or f.proposed_grade
        if effective in grades:
            grades[effective] += 1

    return FindingsSummary(
        total=len(findings),
        **counts,
        **grades,
        # The only count that actually blocks a certificate. Reporting it separately
        # stops a report implying every gap is equally serious.
        blocking=grades["major_nc"],
    )


@router.get("/organizations/{organization_id}/standards/{standard}/findings", response_model=list[FindingRead])
def get_findings(
    organization_id: uuid.UUID,
    standard: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor_org_access),
) -> list[FindingRead]:
    return load_findings(db, organization_id, standard)


@router.get("/organizations/{organization_id}/standards/{standard}/report", response_model=FindingsReportRead)
def get_findings_report(
    organization_id: uuid.UUID,
    standard: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor_org_access),
) -> FindingsReportRead:
    findings = load_findings(db, organization_id, standard)
    return FindingsReportRead(
        findings=findings,
        overall=summarize_findings(findings),
        controls=summarize_findings(findings, requirement_type="control"),
    )


@router.patch("/findings/{finding_id}", response_model=FindingRead)
def patch_finding(
    finding_id: uuid.UUID,
    payload: FindingReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FindingRead:
    # Matches the review-comments restriction — only auditors act on findings.
    if current_user.persona != "auditor":
        raise HTTPException(status_code=403, detail="Only auditors can review findings")

    # Fetch before review_finding, since a "delete" action removes the row —
    # need the clause reference to still build a valid not_assessed response after.
    clause_before_delete = None
    if payload.action == "delete":
        existing = get_finding(db, finding_id)
        clause_before_delete = existing.clause if existing is not None else None

    finding = review_finding(
        db,
        finding_id=finding_id,
        action=payload.action,
        reviewed_by=current_user.id,
        status=payload.status,
        relevance_score=payload.relevance_score,
        coverage_score=payload.coverage_score,
        grade=payload.grade,
    )
    if finding is None:
        raise HTTPException(status_code=404, detail="No such finding")

    if payload.action == "delete":
        logger.info("finding %s deleted by %s", finding_id, current_user.id)
        # The row is gone — build the "not_assessed" shape directly rather
        # than re-fetching a Finding that no longer exists.
        return _build_finding_read(clause_before_delete, None, {}, {})

    logger.info("finding %s saved (reviewed) by %s", finding_id, current_user.id)

    documents_by_id = get_documents_by_ids(db, finding.evidence_document_ids or [])
    extractions_by_doc_id = get_extractions_for_documents(db, finding.evidence_document_ids or [])
    return _build_finding_read(finding.clause, finding, documents_by_id, extractions_by_doc_id)


@router.patch("/findings/{finding_id}/applicability", response_model=FindingRead)
def patch_finding_applicability(
    finding_id: uuid.UUID,
    payload: ApplicabilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FindingRead:
    """Mark an Annex A control applicable or not — the Statement of Applicability
    decision, per clause 6.1.3.

    Rejected for clauses 4-10: they are mandatory requirements of the management
    system and no organisation may exclude one. Excluding a control requires a written
    justification; without a risk register that justification is the auditor's
    assertion, not something the system derives, so it is recorded as their words.
    """
    if current_user.persona != "auditor":
        raise HTTPException(status_code=403, detail="Only auditors can set applicability")

    try:
        finding = set_applicability(
            db,
            finding_id=finding_id,
            is_applicable=payload.is_applicable,
            note=payload.note,
            decided_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    logger.info(
        "finding %s applicability set to %s by %s", finding_id, payload.is_applicable, current_user.id
    )
    documents_by_id = get_documents_by_ids(db, finding.evidence_document_ids or [])
    extractions = get_extractions_for_documents(db, finding.evidence_document_ids or [])
    return _build_finding_read(finding.clause, finding, documents_by_id, extractions)


@router.get("/findings/{finding_id}/evidence", response_model=FindingEvidenceRead)
def get_finding_evidence(
    finding_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor),
) -> FindingEvidenceRead:
    """The per-document evidence behind one finding — a verbatim quote and its location
    for each contributing document.

    The finding's own `rationale` is the reduce step's merged narrative: prose *about*
    several documents rather than a quote *from* one. It reads well as a summary but it
    cannot be located in any document, so a multi-document finding otherwise shows a
    list of names and an unverifiable paragraph. On a real 31-document run, 11 of 50
    multi-document findings had no resolvable location, while 363 of 364 per-document
    mappings did — the citations existed, they just weren't reachable.

    An auditor confirming a nonconformity has to be able to open the passage.
    """
    finding = get_finding(db, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    items: list[FindingEvidenceItem] = []
    if finding.analysis_run_id is not None:
        for row in list_for_clause(db, run_id=finding.analysis_run_id, clause_id=finding.clause_id):
            items.append(
                FindingEvidenceItem(
                    document_id=row.document_id,
                    document_name=row.document.document_name,
                    file_name=row.document.file_name,
                    coverage_score=float(row.coverage_score) if row.coverage_score is not None else None,
                    quote=row.rationale,
                    source_location=row.source_location,
                    unmet_guidance_points=row.unmet_guidance_points or [],
                )
            )

    return FindingEvidenceRead(
        code=finding.clause.code,
        title=finding.clause.title,
        summary=finding.rationale,
        run_id=finding.analysis_run_id,
        items=items,
    )
