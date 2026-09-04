# Pydantic models for the LLM's structured output (ClauseEvaluation, etc.).

from typing import Literal

from pydantic import BaseModel, Field


VERDICTS = ("met", "partial", "unmet")


class ObligationVerdict(BaseModel):
    """One answer to one obligation, with the passage behind it.

    This replaces the model-chosen coverage percentage. The model answers narrow
    questions; the score is counted from the answers in app/ai/scoring.py. Across
    1,057 mappings under the old design only 30 distinct percentages appeared out of
    101 and 98% were multiples of 5 — the number was picked from a mental menu, and
    no explanation of it could be more than decoration.
    """

    index: int = Field(ge=0)
    verdict: Literal["met", "partial", "unmet"]
    # Required for met/partial, absent for unmet — there is no passage to quote when
    # nothing addresses the obligation.
    quote: str | None = None


class ClauseEvaluation(BaseModel):
    requirement_code: str
    obligations: list[ObligationVerdict] = []
    # Set in code from the verdicts (app/ai/scoring.py), never by the model.
    coverage_score: float | None = None
    # The strongest supporting quote, carried for the citation lookup and the
    # document-level summary line.
    rationale: str | None = None
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


