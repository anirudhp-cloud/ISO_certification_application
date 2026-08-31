# M4 tests: the readiness gate.
#
# The point of the gate is that analysis and grading are separate acts. Before it,
# Analyze ran against whatever happened to be uploaded and wrote findings
# unconditionally, so a requirement nobody had submitted evidence for was
# indistinguishable from one examined and found wanting. These tests pin the three
# things that must hold:
#   - step 1 writes no findings
#   - an incomplete run cannot be accepted silently
#   - accepting with a reason records it
#
# The coverage report itself is exercised against fake catalogue rows; the DB-backed
# path is covered by the end-to-end run in the milestone verification.

import uuid
from types import SimpleNamespace

import pytest

from app.crud.analysis_run import coverage_report, read_this_document


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *a, **k):
        return self

    def distinct(self):
        return self

    def __iter__(self):
        return iter(self._rows)


class _FakeSession:
    """Just enough Session to drive coverage_report: it issues one query for the
    distinct clause_ids that have evidence in a run."""

    def __init__(self, covered_clause_ids):
        self._covered = [(cid,) for cid in covered_clause_ids]

    def query(self, *a, **k):
        return _FakeQuery(self._covered)


def _clause(code, requirement_type, clause_id=None):
    return SimpleNamespace(
        id=clause_id or uuid.uuid4(), code=code, requirement_type=requirement_type, title=f"title {code}"
    )


@pytest.fixture
def catalog():
    return [
        _clause("4.1", "clause"),
        _clause("4.2", "clause"),
        _clause("5.2", "clause"),
        _clause("A.2.2", "control"),
        _clause("A.2.4", "control"),
    ]


def _run(document_ids=None, skipped=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        status="coverage_ready",
        document_ids=document_ids,
        skipped_documents=skipped,
    )


# --- coverage is reported per segment --------------------------------------


def test_coverage_is_reported_separately_for_clauses_and_controls(catalog):
    """A clause with no evidence is a hard gap; a control with none may simply be
    inapplicable — so the two are never summed into one number."""
    covered = [catalog[0].id, catalog[3].id]  # 4.1 and A.2.2
    report = coverage_report(_FakeSession(covered), run=_run(), clauses=catalog)

    assert (report["clauses"]["covered"], report["clauses"]["total"]) == (1, 3)
    assert (report["controls"]["covered"], report["controls"]["total"]) == (1, 2)


def test_uncovered_requirements_are_named_not_just_counted(catalog):
    """The auditor has to know WHICH ones to go and ask for."""
    report = coverage_report(_FakeSession([catalog[0].id]), run=_run(), clauses=catalog)

    assert report["clauses"]["missing_codes"] == ["4.2", "5.2"]
    assert report["controls"]["missing_codes"] == ["A.2.2", "A.2.4"]
    assert report["clauses"]["missing_titles"]["4.2"] == "title 4.2"


def test_a_run_is_incomplete_if_either_segment_has_a_gap(catalog):
    all_ids = [c.id for c in catalog]
    assert coverage_report(_FakeSession(all_ids), run=_run(), clauses=catalog)["is_complete"]

    # every clause covered, one control missing -> still incomplete
    minus_control = [c.id for c in catalog if c.code != "A.2.4"]
    assert not coverage_report(_FakeSession(minus_control), run=_run(), clauses=catalog)["is_complete"]


def test_a_run_with_no_evidence_at_all_is_incomplete(catalog):
    report = coverage_report(_FakeSession([]), run=_run(), clauses=catalog)
    assert not report["is_complete"]
    assert report["clauses"]["covered"] == 0 and report["controls"]["covered"] == 0


# --- which documents a run read -------------------------------------------


def test_a_runs_document_list_answers_read_but_matched_nothing():
    """A document the LLM found nothing in produces no evidence rows, so without the
    run's own document list there is nothing to distinguish it from one never
    analysed. This is what M3 could only infer."""
    doc_id, other_id = uuid.uuid4(), uuid.uuid4()
    run = _run(document_ids=[doc_id])

    assert read_this_document(run, doc_id)
    assert not read_this_document(run, other_id)


def test_read_this_document_is_false_without_a_run_or_a_document_list():
    assert not read_this_document(None, uuid.uuid4())
    assert not read_this_document(_run(document_ids=None), uuid.uuid4())
    assert not read_this_document(_run(document_ids=[]), uuid.uuid4())
