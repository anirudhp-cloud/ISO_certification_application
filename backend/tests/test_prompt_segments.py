# M1 tests: the clause/control prompt split, the segment-aware catalogue formatter,
# and the requirement-code validation that stops hallucinated codes vanishing
# silently (ai_iso_plan_27_08_2026.md section 9).

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai.clause_mapper import _keep_known_codes
from app.ai.requirement_catalog import format_requirements_listing, split_by_segment
from app.ai.schemas import ClauseEvaluation, ObligationVerdict, SegmentedMapping
from prompt_library import CLAUSE, CONTROL, get_system_prompt, has_segment

SEED = Path(__file__).resolve().parent.parent.parent / "seed_data" / "iso42001_requirements.json"


def _catalog() -> list[SimpleNamespace]:
    """Clause-like rows straight from the seed file, so these tests exercise the real
    catalogue rather than a hand-written stand-in."""
    data = json.loads(SEED.read_text(encoding="utf-8"))
    return [
        SimpleNamespace(
            code=r["code"],
            sort_order=i,
            requirement_type=r["requirement_type"],
            category=r.get("category"),
            title=r["title"],
            description=r.get("description"),
            evidence_requirements=r.get("evidence_requirements"),
            implementation_guidance=r.get("implementation_guidance"),
            # Omitting this field here is how the prompt gap went unnoticed: the
            # stand-in row had no obligations, so no test could observe that the
            # formatter never printed them.
            obligations=r.get("obligations"),
        )
        for i, r in enumerate(data["requirements"], start=1)
    ]


@pytest.fixture(scope="module")
def catalog():
    return _catalog()


# --- segment split ----------------------------------------------------------


def test_seed_splits_into_32_clauses_and_38_controls(catalog):
    grouped = split_by_segment(catalog)
    assert len(grouped[CLAUSE]) == 32
    assert len(grouped[CONTROL]) == 38


def test_split_preserves_display_order(catalog):
    grouped = split_by_segment(catalog)
    assert [c.code for c in grouped[CLAUSE]][:4] == ["4.1", "4.2", "4.3", "4.4"]
    assert grouped[CLAUSE][-1].code == "10.2"
    assert grouped[CONTROL][0].code == "A.2.2"
    assert grouped[CONTROL][-1].code == "A.10.4"


def test_no_control_codes_leak_into_the_clause_segment(catalog):
    grouped = split_by_segment(catalog)
    assert not any(c.code.startswith("A.") for c in grouped[CLAUSE])
    assert all(c.code.startswith("A.") for c in grouped[CONTROL])


# --- catalogue formatting ---------------------------------------------------


def test_clause_listing_carries_no_annex_b_guidance(catalog):
    grouped = split_by_segment(catalog)
    listing = format_requirements_listing(grouped[CLAUSE], CLAUSE)
    assert "Implementation guidance" not in listing
    assert "5.2" in listing and "AI policy" in listing


def test_control_listing_carries_annex_b_guidance(catalog):
    grouped = split_by_segment(catalog)
    listing = format_requirements_listing(grouped[CONTROL], CONTROL)
    assert "Implementation guidance (Annex B" in listing
    assert "The AI policy should be informed by business strategy." in listing


def test_every_requirement_ships_its_numbered_obligations(catalog):
    """The prompt asks for a verdict per obligation INDEX, so the indexed list has to
    be in the prompt.

    It wasn't. The obligations sat in the database driving every score while the model
    was shown only title/description/evidence, and asked for {"index": n, ...} against
    a list it had never seen. The result, across 668 stored mappings: every single one
    answered index 0 and 544 answered nothing else — one holistic guess wearing an
    obligation's clothes.
    """
    for segment in (CLAUSE, CONTROL):
        requirements = split_by_segment(catalog)[segment]
        listing = format_requirements_listing(requirements, segment)
        assert "Obligations (judge each one separately" in listing
        for requirement in requirements:
            for index, text in enumerate(requirement.obligations or []):
                assert f"[{index}] {text}" in listing, (
                    f"{requirement.code} obligation {index} missing from the {segment} prompt"
                )


def test_obligation_indices_are_contiguous_from_zero(catalog):
    """An index the model returns is looked up positionally (app/ai/rollup.py), so a
    gap in the printed numbering would bind a verdict to the wrong obligation."""
    for requirement in catalog:
        listing = format_requirements_listing([requirement], requirement.requirement_type)
        printed = [
            int(line.strip()[1:].split("]")[0])
            for line in listing.splitlines()
            if line.strip().startswith("[")
        ]
        assert printed == list(range(len(requirement.obligations or [])))


def test_splitting_the_catalogue_does_not_inflate_the_prompt(catalog):
    """The whole case for two passes is that it's free: the catalogue splits along
    with the prompt, so combined input size is unchanged."""
    grouped = split_by_segment(catalog)
    clause_listing = format_requirements_listing(grouped[CLAUSE], CLAUSE)
    control_listing = format_requirements_listing(grouped[CONTROL], CONTROL)
    combined = format_requirements_listing(catalog, CONTROL)

    split_total = len(clause_listing) + len(control_listing)
    # Within 2% of the single combined listing (differs only by the second heading
    # line and the guidance skipped for clauses, which was always empty anyway).
    assert abs(split_total - len(combined)) / len(combined) < 0.02


# --- prompt registry --------------------------------------------------------


def test_each_segment_resolves_to_its_own_versioned_prompt():
    clause_prompt, clause_version = get_system_prompt("iso42001", CLAUSE)
    control_prompt, control_version = get_system_prompt("iso42001", CONTROL)

    assert clause_version == "iso42001-clause-v3"
    assert control_version == "iso42001-control-v3"
    assert clause_prompt != control_prompt


def test_clause_prompt_excludes_annex_a_and_control_prompt_excludes_clauses():
    clause_prompt, _ = get_system_prompt("iso42001", CLAUSE)
    control_prompt, _ = get_system_prompt("iso42001", CONTROL)

    assert "Annex A controls are NOT in scope" in clause_prompt
    assert "unmet_guidance_points" not in clause_prompt
    assert "Clauses 4-10 are NOT in scope" in control_prompt
    assert "unmet_guidance_points" in control_prompt


def test_iso9001_has_no_control_segment():
    """ISO 9001 has no Annex A, so asking for its control pass is an error rather
    than an empty prompt."""
    assert has_segment("iso9001", CLAUSE)
    assert not has_segment("iso9001", CONTROL)
    with pytest.raises(ValueError, match="no 'control' segment"):
        get_system_prompt("iso9001", CONTROL)


def test_unknown_standard_and_segment_are_rejected():
    with pytest.raises(ValueError, match="Unknown standard id"):
        get_system_prompt("iso14001", CLAUSE)
    with pytest.raises(ValueError, match="Unknown segment"):
        get_system_prompt("iso42001", "annex_z")


# --- requirement-code validation -------------------------------------------


def _evaluation(code: str) -> ClauseEvaluation:
    return ClauseEvaluation(
        requirement_code=code,
        obligations=[ObligationVerdict(index=0, verdict="met", quote="q")],
    )


def test_codes_outside_the_segment_catalogue_are_dropped(caplog):
    kept = _keep_known_codes(
        [_evaluation("5.2"), _evaluation("A.6.2.9"), _evaluation("4.99")],
        {"5.2", "4.1"},
        segment="clause",
        document_name="AI_Policy.docx",
    )
    assert [e.requirement_code for e in kept] == ["5.2"]


def test_dropped_codes_are_logged_not_silent(caplog):
    with caplog.at_level("WARNING"):
        _keep_known_codes([_evaluation("A.6.2.9")], {"5.2"}, segment="clause", document_name="AI_Policy.docx")
    assert "A.6.2.9" in caplog.text
    assert "AI_Policy.docx" in caplog.text


def test_valid_codes_pass_through_untouched():
    evaluations = [_evaluation("A.2.2"), _evaluation("A.2.4")]
    kept = _keep_known_codes(evaluations, {"A.2.2", "A.2.4"}, segment="control", document_name="d.docx")
    assert kept == evaluations


# --- SegmentedMapping ------------------------------------------------------


def test_segmented_mapping_flattens_both_segments():
    mapping = SegmentedMapping(clauses=[_evaluation("5.2")], controls=[_evaluation("A.2.2")])
    assert [e.requirement_code for e in mapping.all_mappings()] == ["5.2", "A.2.2"]


def test_segmented_mapping_defaults_to_empty():
    mapping = SegmentedMapping()
    assert mapping.all_mappings() == []
    assert mapping.prompt_versions == {}
