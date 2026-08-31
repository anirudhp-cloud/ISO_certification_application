# Map step — TWO LLM calls per document: one against the standard's mandatory
# clauses, one against its Annex A controls. Fully automatic / content-based:
# nothing about which requirements a document might satisfy is ever supplied by
# the uploader, so every active document has to be read by the LLM once per
# segment per gap-analysis run (see app/tasks/run_gap_analysis.py).
#
# Why two calls rather than one over the combined 70 requirements: clauses 4-10 are
# mandatory and carry no Annex B guidance, while Annex A controls are excludable and
# carry 248 guidance points. Sending them together meant the clause evaluation was
# instructed about a field that is always empty for clauses. The split costs ~5
# tokens of input in total (3,472 + 10,884 vs 14,351 combined), because the catalogue
# splits along with the prompt.

import logging

from app.ai.openai_client import get_control_mappings
from app.ai.requirement_catalog import split_by_segment
from app.ai.schemas import ClauseEvaluation, SegmentedMapping
from app.models.clause import Clause
from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from prompt_library import SEGMENTS, has_segment

logger = logging.getLogger(f"iso_platform.{__name__}")


def _keep_known_codes(
    evaluations: list[ClauseEvaluation], valid_codes: set[str], *, segment: str, document_name: str
) -> list[ClauseEvaluation]:
    """Drop mappings whose requirement_code isn't in this segment's catalogue.

    The model is told not to cross segments, but requirement_code is free text on the
    wire. An unrecognised code used to be kept and then silently discarded downstream
    — the reduce step iterates the catalogue, so a mapping keyed to a code no clause
    matches was never read, and the run log still counted it. Dropping it loudly here
    means a prompt regression shows up in the log instead of as quiet under-coverage.
    """
    kept, dropped = [], []
    for evaluation in evaluations:
        (kept if evaluation.requirement_code in valid_codes else dropped).append(evaluation)
    if dropped:
        logger.warning(
            "%s pass on %s: dropped %d mapping(s) with codes outside this segment's catalogue: %s",
            segment, document_name, len(dropped), ", ".join(sorted(e.requirement_code for e in dropped)),
        )
    return kept


def map_document(
    document: Document,
    extraction: DocumentExtraction | None,
    clauses: list[Clause],
    *,
    certification_standard: str,
) -> SegmentedMapping:
    """Every requirement this one document's extracted text provides evidence for,
    split by segment and evaluated against `clauses` (the standard's full seeded
    catalog). Returns empty segments (no LLM calls) if there's no usable text yet —
    extraction failed, hasn't run, or Document Intelligence wasn't configured.

    `certification_standard` is the ONE standard currently being analyzed
    (matching `clauses`) — a document can now be tagged with several standards
    at once (see app/models/document.py), so it can't be read off the document
    itself; the caller (app/tasks/run_gap_analysis.py) already knows which one
    this run is for."""
    if extraction is None or extraction.extraction_method == "ocr_unavailable" or not extraction.extracted_text.strip():
        return SegmentedMapping()

    by_segment = split_by_segment(clauses)
    result = SegmentedMapping()

    for segment in SEGMENTS:
        segment_clauses = by_segment[segment]
        if not segment_clauses:
            # ISO 9001 has no Annex A, and a standard part-way through seeding may be
            # missing one side. Never send an empty catalogue to the LLM.
            continue
        if not has_segment(certification_standard, segment):
            logger.info("%s has no '%s' prompt — skipping that pass", certification_standard, segment)
            continue

        mapping_result, prompt_version = get_control_mappings(
            certification_standard,
            extraction.extracted_text,
            segment_clauses,
            segment,
            label=document.document_name,
        )
        result.prompt_versions[segment] = prompt_version
        setattr(
            result,
            f"{segment}s",
            _keep_known_codes(
                mapping_result.mappings,
                {c.code for c in segment_clauses},
                segment=segment,
                document_name=document.document_name,
            ),
        )

    logger.info(
        "mapped %s: %d clause mapping(s), %d control mapping(s)",
        document.document_name, len(result.clauses), len(result.controls),
    )
    return result
