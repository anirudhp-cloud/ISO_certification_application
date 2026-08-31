# Reduce/combine step — for one clause, turns however many documents' map-step
# results named it into a single Finding. Called once per clause, for every
# clause in the standard, by app/tasks/run_gap_analysis.py — including clauses
# with zero contributors this run, so a finding whose only backing document was
# deleted correctly drops back to 'not_assessed' (see reset_finding_if_auto).

import uuid

from sqlalchemy.orm import Session

from app.ai.openai_client import combine_contributions
from app.ai.schemas import ClauseEvaluation
from app.crud.finding import reset_finding_if_auto, upsert_finding_from_mapping
from app.models.clause import Clause
from app.models.document import Document

Contribution = tuple[Document, ClauseEvaluation]


def reduce_clause(
    db: Session,
    *,
    organization_id: uuid.UUID,
    certification_standard: str,
    clause: Clause,
    contributions: list[Contribution],
    analysis_run_id: uuid.UUID | None = None,
) -> None:
    if not contributions:
        reset_finding_if_auto(db, organization_id=organization_id, clause_id=clause.id)
        return

    if len(contributions) == 1:
        document, evaluation = contributions[0]
        relevance_score = evaluation.relevance_score
        coverage_score = evaluation.coverage_score
        rationale = evaluation.rationale
        unmet_guidance_points = evaluation.unmet_guidance_points
        primary_document_id = document.id
    else:
        combined = combine_contributions(
            clause.code,
            clause.title,
            clause.description,
            [
                {
                    "document_name": document.document_name,
                    "relevance_score": evaluation.relevance_score,
                    "coverage_score": evaluation.coverage_score,
                    "rationale": evaluation.rationale,
                    "unmet_guidance_points": evaluation.unmet_guidance_points,
                }
                for document, evaluation in contributions
            ],
        )
        relevance_score = combined.relevance_score
        coverage_score = combined.coverage_score
        rationale = combined.rationale
        unmet_guidance_points = combined.unmet_guidance_points
        # Primary = whichever single document scored highest on its own — used
        # only for the "open the source document" single-click-through link;
        # evidence_document_ids (below) carries the full contributing set.
        primary_document_id = max(contributions, key=lambda pair: pair[1].coverage_score)[0].id

    upsert_finding_from_mapping(
        db,
        organization_id=organization_id,
        certification_standard=certification_standard,
        clause=clause,
        analysis_run_id=analysis_run_id,
        evidence_document_id=primary_document_id,
        evidence_document_ids=[document.id for document, _ in contributions],
        relevance_score=relevance_score,
        coverage_score=coverage_score,
        rationale=rationale,
        unmet_guidance_points=unmet_guidance_points,
    )
