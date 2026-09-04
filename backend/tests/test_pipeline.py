# M2 tests: the two-pass map step and per-document persistence, with the Azure
# OpenAI client stubbed out. These are the regression net for the pipeline rewrite —
# before M2 the only file under tests/ was a script that printed a prompt.
#
# No database and no network: map_document is exercised directly against fake
# clause rows, and record_mappings against a fake session that just collects what
# was added. What's being pinned is the wiring — two calls not one, correct segment
# tagging, citations resolved at write time, unknown codes dropped — not SQLAlchemy.

import uuid
from types import SimpleNamespace

import pytest

from app.ai import clause_mapper
from app.ai.schemas import ClauseEvaluation, MappingResult, ObligationVerdict
from app.crud import evidence_mapping as evidence_crud

CLAUSE_CODES = ["4.1", "5.2"]
CONTROL_CODES = ["A.2.2", "A.2.4"]


def _clause(code: str, order: int):
    return SimpleNamespace(
        id=uuid.uuid4(),
        code=code,
        sort_order=order,
        requirement_type="control" if code.startswith("A.") else "clause",
        category="cat",
        title=f"title {code}",
        description=f"description {code}",
        evidence_requirements=["something documented"],
        implementation_guidance=["a guidance point"] if code.startswith("A.") else None,
        # The mark scheme. Two obligations, so a document satisfying one scores 1 of 2
        # — the score is a count of these, never a number the model supplies.
        obligations=[f"first obligation of {code}", f"second obligation of {code}"],
    )


@pytest.fixture
def catalog():
    codes = CLAUSE_CODES + CONTROL_CODES
    return [_clause(code, i) for i, code in enumerate(codes, start=1)]


@pytest.fixture
def document():
    return SimpleNamespace(id=uuid.uuid4(), document_name="AI_Policy.docx")


@pytest.fixture
def extraction():
    return SimpleNamespace(
        extraction_method="native",
        extracted_text="This Policy shall be reviewed at least annually by the Chief AI Officer.",
        extracted_chunks=[
            {"location": 'Section "7. Policy Review", paragraph 1',
             "text": "This Policy shall be reviewed at least annually by the Chief AI Officer."},
            {"location": 'Section "1. Purpose", paragraph 1', "text": "This policy sets out our commitment."},
        ],
    )


class _StubLLM:
    """Records each call's segment and returns whatever was queued for it."""

    def __init__(self, by_segment: dict[str, list[ClauseEvaluation]]):
        self.by_segment = by_segment
        self.calls: list[tuple[str, int]] = []

    def __call__(self, standard_id, document_text, clauses, segment, *, label=None):
        self.calls.append((segment, len(clauses)))
        return MappingResult(mappings=self.by_segment.get(segment, [])), f"stub-{segment}-v1"


def _evaluation(code: str, *, verdicts=None, unmet=None, rationale="This policy sets out our commitment."):
    """An evaluation as the model now returns one: obligation verdicts and quotes, no
    score. `verdicts` defaults to satisfying only the first of two obligations."""
    return ClauseEvaluation(
        requirement_code=code,
        obligations=verdicts
        if verdicts is not None
        else [
            ObligationVerdict(index=0, verdict="met", quote=rationale),
            ObligationVerdict(index=1, verdict="unmet"),
        ],
        unmet_guidance_points=unmet or [],
    )


# --- the two-pass map step -------------------------------------------------


def test_one_document_triggers_one_call_per_segment(monkeypatch, catalog, document, extraction):
    stub = _StubLLM({"clause": [_evaluation("5.2")], "control": [_evaluation("A.2.2")]})
    monkeypatch.setattr(clause_mapper, "get_control_mappings", stub)

    clause_mapper.map_document(document, extraction, catalog, certification_standard="iso42001")

    assert [segment for segment, _ in stub.calls] == ["clause", "control"]


def test_each_pass_receives_only_its_own_segment_of_the_catalogue(monkeypatch, catalog, document, extraction):
    stub = _StubLLM({})
    monkeypatch.setattr(clause_mapper, "get_control_mappings", stub)

    clause_mapper.map_document(document, extraction, catalog, certification_standard="iso42001")

    sizes = dict(stub.calls)
    assert sizes["clause"] == len(CLAUSE_CODES)
    assert sizes["control"] == len(CONTROL_CODES)


def test_results_land_in_the_segment_that_produced_them(monkeypatch, catalog, document, extraction):
    stub = _StubLLM({"clause": [_evaluation("5.2")], "control": [_evaluation("A.2.2"), _evaluation("A.2.4")]})
    monkeypatch.setattr(clause_mapper, "get_control_mappings", stub)

    result = clause_mapper.map_document(document, extraction, catalog, certification_standard="iso42001")

    assert [e.requirement_code for e in result.clauses] == ["5.2"]
    assert [e.requirement_code for e in result.controls] == ["A.2.2", "A.2.4"]
    assert result.prompt_versions == {"clause": "stub-clause-v1", "control": "stub-control-v1"}


def test_a_control_code_returned_by_the_clause_pass_is_dropped(monkeypatch, catalog, document, extraction):
    """The clause prompt forbids Annex A codes, but requirement_code is free text on
    the wire — a leaked code must not be kept."""
    stub = _StubLLM({"clause": [_evaluation("5.2"), _evaluation("A.2.2")], "control": []})
    monkeypatch.setattr(clause_mapper, "get_control_mappings", stub)

    result = clause_mapper.map_document(document, extraction, catalog, certification_standard="iso42001")

    assert [e.requirement_code for e in result.clauses] == ["5.2"]


def test_no_llm_calls_when_there_is_no_usable_text(monkeypatch, catalog, document):
    stub = _StubLLM({})
    monkeypatch.setattr(clause_mapper, "get_control_mappings", stub)

    for unusable in (
        None,
        SimpleNamespace(extraction_method="ocr_unavailable", extracted_text="", extracted_chunks=None),
        SimpleNamespace(extraction_method="native", extracted_text="   ", extracted_chunks=None),
    ):
        result = clause_mapper.map_document(document, unusable, catalog, certification_standard="iso42001")
        assert result.all_mappings() == []

    assert stub.calls == []


def test_a_standard_with_no_controls_runs_only_the_clause_pass(monkeypatch, document, extraction):
    """ISO 9001 has no Annex A — the control pass must be skipped, not sent an empty
    catalogue."""
    stub = _StubLLM({"clause": [_evaluation("4.1")]})
    monkeypatch.setattr(clause_mapper, "get_control_mappings", stub)
    clauses_only = [_clause(code, i) for i, code in enumerate(CLAUSE_CODES, start=1)]

    result = clause_mapper.map_document(document, extraction, clauses_only, certification_standard="iso9001")

    assert [segment for segment, _ in stub.calls] == ["clause"]
    assert result.controls == []


# --- per-document persistence ---------------------------------------------


class _FakeSession:
    def __init__(self):
        self.added = []

    def add(self, row):
        self.added.append(row)


def test_mappings_are_written_with_their_segment(catalog, document, extraction):
    db = _FakeSession()
    rows = evidence_crud.record_mappings(
        db,
        run_id=uuid.uuid4(),
        document_id=document.id,
        clauses_by_code={c.code: c for c in catalog},
        evaluations_by_segment={"clause": [_evaluation("5.2")], "control": [_evaluation("A.2.2")]},
        chunks=extraction.extracted_chunks,
    )

    assert len(rows) == 2
    assert {r.segment for r in rows} == {"clause", "control"}
    assert db.added == rows


def test_citation_is_resolved_at_write_time(catalog, document, extraction):
    db = _FakeSession()
    rows = evidence_crud.record_mappings(
        db,
        run_id=uuid.uuid4(),
        document_id=document.id,
        clauses_by_code={c.code: c for c in catalog},
        evaluations_by_segment={
            "clause": [_evaluation("5.2", rationale="This Policy shall be reviewed at least annually")]
        },
        chunks=extraction.extracted_chunks,
    )

    assert rows[0].source_location == 'Section "7. Policy Review", paragraph 1'


def test_unmatchable_quote_stores_no_location_rather_than_failing(catalog, document, extraction):
    """Expected for OCR'd documents: that path yields no positional chunks."""
    db = _FakeSession()
    rows = evidence_crud.record_mappings(
        db,
        run_id=uuid.uuid4(),
        document_id=document.id,
        clauses_by_code={c.code: c for c in catalog},
        evaluations_by_segment={"clause": [_evaluation("5.2", rationale="text that is not in the document")]},
        chunks=None,
    )

    assert rows[0].source_location is None


def test_empty_guidance_points_are_stored_as_null_not_empty_array(catalog, document, extraction):
    db = _FakeSession()
    rows = evidence_crud.record_mappings(
        db,
        run_id=uuid.uuid4(),
        document_id=document.id,
        clauses_by_code={c.code: c for c in catalog},
        evaluations_by_segment={
            "control": [_evaluation("A.2.2"), _evaluation("A.2.4", unmet=["a guidance point"])]
        },
        chunks=extraction.extracted_chunks,
    )

    assert rows[0].unmet_guidance_points is None
    assert rows[1].unmet_guidance_points == ["a guidance point"]


def test_a_code_missing_from_the_catalogue_produces_no_orphan_row(catalog, document, extraction):
    db = _FakeSession()
    rows = evidence_crud.record_mappings(
        db,
        run_id=uuid.uuid4(),
        document_id=document.id,
        clauses_by_code={c.code: c for c in catalog},
        evaluations_by_segment={"clause": [_evaluation("9.9.9")]},
        chunks=extraction.extracted_chunks,
    )

    assert rows == []
    assert db.added == []


def test_verdicts_and_quotes_are_carried_through(catalog, document, extraction):
    db = _FakeSession()
    rows = evidence_crud.record_mappings(
        db,
        run_id=(run := uuid.uuid4()),
        document_id=document.id,
        clauses_by_code={c.code: c for c in catalog},
        evaluations_by_segment={"clause": [_evaluation("5.2")]},
        chunks=extraction.extracted_chunks,
    )

    row = rows[0]
    assert row.run_id == run
    assert row.document_id == document.id
    assert row.clause_id == next(c.id for c in catalog if c.code == "5.2")
    # Every verdict is stored with the obligation text it answers, so the row is
    # readable without re-joining the catalogue.
    assert [v["verdict"] for v in row.obligation_verdicts] == ["met", "unmet"]
    assert row.obligation_verdicts[0]["obligation"] == "first obligation of 5.2"
    assert row.rationale == "This policy sets out our commitment."
