# Pydantic schemas for reading back one document's clause and control structure —
# the per-document view (M3 in ai_iso_plan_27_08_2026.md).
#
# Split into two lists rather than one flat list because the two segments mean
# different things to a reader: the 32 clauses are mandatory and can never be
# excluded, the 38 Annex A controls are excludable and carry Annex B guidance. The
# response also reports each segment's total so the UI can say "3 of 32" without
# hardcoding a count that differs per standard.

import uuid
from datetime import datetime

from pydantic import BaseModel


class RequirementMappingRead(BaseModel):
    """One requirement this document provides evidence for."""

    code: str
    title: str
    category: str | None
    relevance_score: float | None
    coverage_score: float | None
    # The LLM's verbatim quote from this document.
    rationale: str | None
    # Where that quote sits, e.g. 'Section "7. Policy Review", paragraph 1'. None when
    # the quote couldn't be matched back — expected for OCR'd documents, which produce
    # no positional chunks.
    source_location: str | None
    # Annex B points judged unsatisfied. Always empty for clauses, which have no Annex B.
    unmet_guidance_points: list[str]
    # How many Annex B points the control has in total, so the UI can render
    # "2 of 12 not satisfied" rather than a bare list. 0 for clauses.
    guidance_points_total: int


class SegmentMappingsRead(BaseModel):
    """One segment's results for this document."""

    segment: str  # 'clause' | 'control'
    matched: int  # requirements this document provides evidence for
    total: int  # requirements in this segment of the standard
    mappings: list[RequirementMappingRead]


class DocumentMappingsRead(BaseModel):
    document_id: uuid.UUID
    document_name: str
    file_name: str
    version_number: int
    certification_standard: str
    # 'not_analysed'  — no run has read this document yet
    # 'matched'       — read, and it supports at least one requirement
    # 'no_match'      — read, and it supports none. Usually a misfiled document or the
    #                   wrong standard tag, so the UI must say this rather than showing
    #                   an empty list that looks identical to 'not_analysed'.
    status: str
    # The run these results came from, or the run that read the document and found
    # nothing. None only when status is 'not_analysed'.
    run_id: uuid.UUID | None
    analysed_at: datetime | None
    clauses: SegmentMappingsRead
    controls: SegmentMappingsRead


class FindingEvidenceItem(BaseModel):
    """One document's contribution to one requirement — a verbatim quote and where it
    sits, so an auditor can open the passage rather than trust a summary."""

    document_id: uuid.UUID
    document_name: str
    file_name: str
    coverage_score: float | None
    quote: str | None
    source_location: str | None
    unmet_guidance_points: list[str]


class FindingEvidenceRead(BaseModel):
    code: str
    title: str
    # The reduce step's merged narrative. Useful as an overview, but it is prose about
    # several documents rather than a quote from one, so it is NOT a citation.
    summary: str | None
    run_id: uuid.UUID | None
    # The actual evidence, one row per contributing document.
    items: list[FindingEvidenceItem]
