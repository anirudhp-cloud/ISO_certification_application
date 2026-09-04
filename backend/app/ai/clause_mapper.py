# Map step — TWO LLM calls per document: one against the standard's mandatory
# clauses, one against its Annex A controls. Fully automatic / content-based:
# nothing about which requirements a document might satisfy is ever supplied by
# the uploader, so every active document has to be read by the LLM once per
# segment per gap-analysis run (see app/tasks/run_gap_analysis.py).
#
# Why two calls rather than one over the combined 70 requirements: clauses 4-10 are
# mandatory and carry no Annex B guidance, while Annex A controls are excludable and
# carry 248 guidance points. Sending them together meant the clause evaluation was
# instructed about a field that is always empty for clauses. The split costs almost
# nothing (5,306 + 9,741 tokens) because the catalogue splits along with the prompt.

import logging

from app.ai.openai_client import get_control_mappings
from app.ai.requirement_catalog import split_by_segment
from app.ai.scoring import is_mapped, normalise_evaluation
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


def _dedupe_codes(
    evaluations: list[ClauseEvaluation], *, segment: str, document_name: str
) -> list[ClauseEvaluation]:
    """Collapse repeated requirement_codes down to the best-evidenced one.

    One LLM call covers the whole segment, but requirement_code is free text on the
    wire and the model does sometimes emit the same code twice for a document that
    addresses a requirement in two places. `evidence_mappings` is unique on
    (run_id, document_id, clause_id), so a duplicate pair used to raise
    UniqueViolation — and because run_gap_analysis.py isolates each document in its
    own try/except, that rolled back the ENTIRE document, silently costing the run
    every mapping that document had. Keeping the highest-coverage entry preserves the
    strongest evidence and makes the collision a log line instead of a lost document.
    """
    best: dict[str, ClauseEvaluation] = {}
    duplicates: list[str] = []
    for evaluation in evaluations:
        existing = best.get(evaluation.requirement_code)
        if existing is None:
            best[evaluation.requirement_code] = evaluation
            continue
        duplicates.append(evaluation.requirement_code)
        if (evaluation.coverage_score or 0) > (existing.coverage_score or 0):
            best[evaluation.requirement_code] = evaluation
    if duplicates:
        logger.warning(
            "%s pass on %s: collapsed %d duplicate mapping(s), kept highest coverage per code: %s",
            segment, document_name, len(duplicates), ", ".join(sorted(set(duplicates))),
        )
    return list(best.values())


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
        obligation_totals = {c.code: len(c.obligations or []) for c in segment_clauses}

        kept = _keep_known_codes(
            mapping_result.mappings,
            {c.code for c in segment_clauses},
            segment=segment,
            document_name=document.document_name,
        )
        # Score each evaluation from its verdicts BEFORE deduping, since dedupe now
        # compares computed coverage.
        scored = [
            normalise_evaluation(e, obligation_totals.get(e.requirement_code, 0)) for e in kept
        ]
        # A document maps to a requirement only if it satisfies an obligation. The
        # model is told to omit an all-unmet requirement, but this enforces it rather
        # than trusting it — an all-unmet mapping would otherwise store a 0% row that
        # reads as "assessed and found lacking" when nothing was evidenced at all.
        mapped = [e for e in scored if is_mapped(e)]
        if len(mapped) != len(scored):
            logger.info(
                "%s pass on %s: dropped %d requirement(s) with no satisfied obligation",
                segment, document.document_name, len(scored) - len(mapped),
            )
        setattr(
            result,
            f"{segment}s",
            _dedupe_codes(mapped, segment=segment, document_name=document.document_name),
        )

    logger.info(
        "mapped %s: %d clause mapping(s), %d control mapping(s)",
        document.document_name, len(result.clauses), len(result.controls),
    )
    return result
