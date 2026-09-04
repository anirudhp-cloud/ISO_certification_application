# Rollup step — for one requirement, turns however many documents' obligation
# verdicts into a single Finding. Called once per requirement, for every requirement
# in the standard, by app/tasks/run_gap_analysis.py — including requirements with zero
# contributors, so a finding whose only backing document was deleted correctly drops
# back to 'not_assessed' (see reset_finding_if_auto).
#
# This used to make an LLM call per multi-document requirement, asking the model to
# merge several results into a prose narrative. That is gone. The narrative was prose
# ABOUT documents rather than a quote FROM one, so it could not be located — 11 of 50
# multi-document findings on a real run had no resolvable citation — and it buried the
# actual audit question inside a paragraph. Obligation verdicts make the merge
# arithmetic: take the strongest verdict per obligation across all documents. No call,
# ~70 fewer requests and ~$0.45 less per run, and every line still traces to a
# passage.

import uuid

from sqlalchemy.orm import Session

from app.ai.grading import propose_grade_from_obligations
from app.ai.rollup import combined_unmet_guidance, roll_up_obligations
from app.crud.finding import reset_finding_if_auto, upsert_finding_from_mapping
from app.models.clause import Clause
from app.models.evidence_mapping import EvidenceMapping

Contribution = tuple[object, EvidenceMapping]


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

    mappings = [mapping for _, mapping in contributions]
    documents = [document for document, _ in contributions]

    rolled = roll_up_obligations(clause.obligations or [], mappings)
    unmet_guidance = combined_unmet_guidance(mappings) if clause.requirement_type == "control" else []

    # Primary = whichever document satisfied the most obligations on its own — used
    # for the "open the source document" click-through; evidence_document_ids carries
    # the full contributing set.
    primary_document = max(
        contributions, key=lambda pair: float(pair[1].coverage_score or 0)
    )[0]

    upsert_finding_from_mapping(
        db,
        organization_id=organization_id,
        certification_standard=certification_standard,
        clause=clause,
        analysis_run_id=analysis_run_id,
        evidence_document_id=primary_document.id,
        evidence_document_ids=[d.id for d in documents],
        coverage_score=rolled["coverage_score"],
        # The requirement-level reasoning: every obligation, its best verdict across
        # all contributing documents, and which documents supplied it. Replaces the
        # merged narrative — including, crucially, naming the obligations no document
        # satisfies, which is the question an auditor is actually asking.
        obligation_rollup=rolled,
        unmet_guidance_points=unmet_guidance or None,
        proposed_grade=propose_grade_from_obligations(
            segment=clause.requirement_type,
            total_obligations=rolled["total_obligations"],
            met=rolled["met"],
            partial=rolled["partial"],
            unmet_guidance_points=unmet_guidance,
        ),
    )
