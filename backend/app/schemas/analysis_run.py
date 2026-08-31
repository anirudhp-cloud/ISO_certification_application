# Pydantic schemas for an analysis run and its coverage report.

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SegmentCoverageRead(BaseModel):
    """One segment's coverage. Reported separately per segment because the two mean
    different things: a mandatory clause with no evidence is a hard gap, while a
    control with none may simply be inapplicable to this organisation."""

    segment: str  # 'clause' | 'control'
    total: int
    covered: int
    # Requirements with no evidence at all from any document in this run — the list
    # the auditor acts on before accepting.
    missing_codes: list[str]
    missing_titles: dict[str, str]


class SkippedDocumentRead(BaseModel):
    """A document this run could not read. Listed explicitly because its absence must
    never be mistaken for the organisation having no evidence — the attempt failed."""

    document_id: str
    document_name: str
    error: str


class AnalysisRunRead(BaseModel):
    # `model_id` collides with pydantic's protected "model_" namespace; it names the
    # LLM deployment, so keep the field and drop the guard.
    model_config = ConfigDict(protected_namespaces=())

    id: uuid.UUID
    organization_id: uuid.UUID
    certification_standard: str
    # 'running' | 'coverage_ready' | 'accepted' | 'failed'
    status: str
    error_message: str | None

    started_at: datetime
    completed_at: datetime | None
    document_count: int

    # What produced these results, so runs under different prompt revisions or models
    # stay distinguishable.
    prompt_version_clause: str | None
    prompt_version_control: str | None
    model_id: str | None

    input_tokens: int | None
    output_tokens: int | None
    cached_tokens: int | None
    cost_usd: float | None

    gate_accepted_at: datetime | None
    gate_override_reason: str | None

    # Documents that could not be read, and how many were. Coverage counts below are
    # only meaningful when nothing was skipped.
    skipped_documents: list[SkippedDocumentRead]
    documents_read: int

    # False when any requirement has no evidence OR any document was skipped —
    # a skipped document makes coverage unknowable, not just lower.
    is_complete: bool
    clauses: SegmentCoverageRead
    controls: SegmentCoverageRead


class RunAcceptRequest(BaseModel):
    # Required only when coverage is incomplete — recorded on the run so
    # "we knowingly assessed on incomplete evidence" is never indistinguishable from
    # a complete assessment.
    override_reason: str | None = None
