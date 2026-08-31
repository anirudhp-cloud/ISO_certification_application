# Pydantic models for the LLM's structured output (ClauseEvaluation, etc.).

from pydantic import BaseModel, Field


class ClauseEvaluation(BaseModel):
    requirement_code: str
    relevance_score: float = Field(ge=0, le=100)
    coverage_score: float = Field(ge=0, le=100)
    rationale: str
    # Verbatim subset of the control's Annex B implementation_guidance points
    # (see app/ai/requirement_catalog.py) that this document's evidence does
    # NOT satisfy. Empty for clauses 4-10 (no Annex B) or full coverage.
    unmet_guidance_points: list[str] = []


class MappingResult(BaseModel):
    mappings: list[ClauseEvaluation]


class SegmentedMapping(BaseModel):
    """One document's results across both LLM passes (see app/ai/clause_mapper.py).

    Kept separate rather than concatenated because the two segments are graded
    differently downstream: a clause can never be excluded, an Annex A control can.
    `prompt_versions` records which prompt revision produced each side, so results
    from different revisions stay distinguishable.
    """

    clauses: list[ClauseEvaluation] = []
    controls: list[ClauseEvaluation] = []
    prompt_versions: dict[str, str] = {}

    def all_mappings(self) -> list[ClauseEvaluation]:
        """Both segments flattened — for callers that key purely by requirement_code
        and don't care which pass found it (e.g. the reduce step, which iterates the
        catalogue and looks each code up)."""
        return [*self.clauses, *self.controls]


class CombinedEvaluation(BaseModel):
    """Output of the reduce/combine step — merges 2+ documents' ClauseEvaluations
    for the same requirement into one assessment (see app/ai/aggregator.py)."""

    relevance_score: float = Field(ge=0, le=100)
    coverage_score: float = Field(ge=0, le=100)
    rationale: str
    unmet_guidance_points: list[str] = []
