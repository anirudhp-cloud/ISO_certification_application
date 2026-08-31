# Pydantic schemas for Finding — read (one row per clause, joined against the
# organization's finding for it, if any) and auditor review actions.

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class EvidenceDocumentRef(BaseModel):
    document_id: uuid.UUID
    document_name: str


class GuidancePointRead(BaseModel):
    text: str
    met: bool


def build_guidance_checklist(
    implementation_guidance: list[str] | None, unmet_points: list[str] | None
) -> list[GuidancePointRead]:
    """Annex B's full guidance-point list for a control, each marked met/unmet
    against `unmet_points` (verbatim strings). Empty for clauses 4-10 (no
    Annex B) or a control with no guidance seeded yet."""
    return [
        GuidancePointRead(text=point, met=point not in (unmet_points or []))
        for point in (implementation_guidance or [])
    ]


class FindingRead(BaseModel):
    clause_id: uuid.UUID
    requirement_type: str  # 'clause' | 'control'
    code: str
    category: str | None
    title: str

    finding_id: uuid.UUID | None = None
    status: str = "not_assessed"
    relevance_score: float | None = None
    coverage_score: float | None = None
    rationale: str | None = None
    # Where `rationale`'s quoted passage actually sits in the source document
    # (e.g. "Page 3, Paragraph 2") — computed deterministically at read time by
    # app/ai/source_locator.py, never persisted. None if it couldn't be located
    # (e.g. OCR'd text has no positional structure, or the quote drifted).
    source_location: str | None = None
    evidence: list[EvidenceDocumentRef] = []
    mapping_method: str | None = None
    reviewed_by: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    guidance_checklist: list[GuidancePointRead] = []

    # --- M5: grading and applicability ---
    # 'no_evidence' | 'insufficient' | 'satisfied'. Derived, not stored — the
    # distinction the old status column could not make: a requirement nobody has
    # submitted evidence for looked identical to one examined and found wanting.
    evidence_state: str = "no_evidence"
    # The machine's suggestion, and the auditor's decision, kept apart so accepting a
    # suggestion is a recorded act rather than an absence of one.
    proposed_grade: str | None = None
    grade: str | None = None
    grade_label: str | None = None
    # Annex A controls only; None for all 32 clauses, which can never be excluded.
    is_applicable: bool | None = None
    applicability_note: str | None = None
    # True when a reviewed finding's backing evidence moved after approval.
    evidence_changed_since_review: bool = False
    analysis_run_id: uuid.UUID | None = None


class FindingsSummary(BaseModel):
    total: int
    met: int
    partial: int
    gap: int
    not_assessed: int
    # Grade counts alongside the legacy status counts. Kept side by side while the
    # frontend migrates off met/partial/gap; `blocking` is the number of major
    # nonconformities, which is the only count that actually blocks a certificate.
    conforming: int = 0
    ofi: int = 0
    minor_nc: int = 0
    major_nc: int = 0
    not_applicable: int = 0
    blocking: int = 0


class FindingsReportRead(BaseModel):
    findings: list[FindingRead]
    overall: FindingsSummary  # all 70 requirements (clauses + controls)
    controls: FindingsSummary  # Annex A controls only (requirement_type == 'control')
    clauses: FindingsSummary | None = None  # mandatory clauses only


class FindingReviewRequest(BaseModel):
    action: Literal["save", "delete"]
    status: str | None = None
    relevance_score: float | None = None
    coverage_score: float | None = None
    # The auditor's grade decision. Separate from `status` so the two rubrics can
    # coexist while the frontend migrates.
    grade: Literal["conforming", "ofi", "minor_nc", "major_nc", "not_applicable"] | None = None


class ApplicabilityRequest(BaseModel):
    """Annex A controls only — clauses 4-10 are mandatory and cannot be excluded."""

    is_applicable: bool
    # Required when is_applicable is false: an exclusion without a stated reason is
    # not one an auditor can defend.
    note: str | None = None
