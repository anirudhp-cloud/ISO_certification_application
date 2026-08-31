# Tests for the three fixes that make a 40-document run viable.
#
# At one document none of these matter. At forty they decide whether the run is worth
# starting: ~80 API calls, and before these fixes the first failure among them
# abandoned every remaining document, committed a partial result, and left no usable
# record of how long anything took.
#
# The governing rule: NO FALLBACK. A document that could not be read produces
# nothing, is recorded as unread, and never becomes "read and matched nothing" —
# because that would attribute a failed call to the organisation's evidence.

import uuid
from types import SimpleNamespace

from app.crud.analysis_run import coverage_report, read_this_document, skipped_document_ids


def _clause(code, requirement_type):
    return SimpleNamespace(
        id=uuid.uuid4(), code=code, requirement_type=requirement_type, title=f"title {code}"
    )


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
    def __init__(self, covered_clause_ids):
        self._covered = [(cid,) for cid in covered_clause_ids]

    def query(self, *a, **k):
        return _FakeQuery(self._covered)


def _run(document_ids, skipped=None):
    return SimpleNamespace(
        id=uuid.uuid4(), status="coverage_ready", document_ids=document_ids, skipped_documents=skipped
    )


def _skip(document_id, name="Risk_Register.xlsx", error="RateLimitError: 429"):
    return {"document_id": str(document_id), "document_name": name, "error": error}


# --- fix 1: a skipped document is recorded, not silently absent --------------


def test_a_skipped_document_is_named_with_its_reason():
    doc = uuid.uuid4()
    report = coverage_report(_FakeSession([]), run=_run([doc], [_skip(doc)]), clauses=[])

    assert len(report["skipped_documents"]) == 1
    assert report["skipped_documents"][0]["document_name"] == "Risk_Register.xlsx"
    assert "RateLimitError" in report["skipped_documents"][0]["error"]


def test_the_report_distinguishes_documents_read_from_documents_attempted():
    read, failed = uuid.uuid4(), uuid.uuid4()
    report = coverage_report(_FakeSession([]), run=_run([read, failed], [_skip(failed)]), clauses=[])

    assert report["documents_total"] == 2
    assert report["documents_read"] == 1


def test_a_run_with_no_skips_reports_none():
    report = coverage_report(_FakeSession([]), run=_run([uuid.uuid4()]), clauses=[])
    assert report["skipped_documents"] == []
    assert report["documents_read"] == report["documents_total"] == 1


# --- no fallback: a skipped document must not read as "matched nothing" ------


def test_a_skipped_document_counts_as_not_read():
    """The whole no-fallback rule in one assertion. The document was in scope, so
    document_ids contains it — but the attempt failed, and claiming it was read and
    matched nothing would assert something that never happened."""
    read, failed = uuid.uuid4(), uuid.uuid4()
    run = _run([read, failed], [_skip(failed)])

    assert read_this_document(run, read)
    assert not read_this_document(run, failed)


def test_skipped_document_ids_parses_the_stored_entries():
    failed = uuid.uuid4()
    assert skipped_document_ids(_run([failed], [_skip(failed)])) == {failed}
    assert skipped_document_ids(_run([failed])) == set()
    assert skipped_document_ids(None) == set()


# --- no fallback: a skip makes coverage unknowable, not merely lower ---------


def test_full_requirement_coverage_is_still_incomplete_when_a_document_was_skipped():
    """Otherwise the gate could wave through a run that never opened the risk
    register, on the strength of requirement counts that cannot mean what they say."""
    catalog = [_clause("4.1", "clause"), _clause("A.2.2", "control")]
    all_covered = [c.id for c in catalog]
    failed = uuid.uuid4()

    complete = coverage_report(_FakeSession(all_covered), run=_run([uuid.uuid4()]), clauses=catalog)
    assert complete["is_complete"]

    with_skip = coverage_report(
        _FakeSession(all_covered), run=_run([uuid.uuid4(), failed], [_skip(failed)]), clauses=catalog
    )
    assert with_skip["clauses"]["missing_codes"] == []
    assert with_skip["controls"]["missing_codes"] == []
    assert not with_skip["is_complete"], "a skipped document must force incomplete coverage"


def test_a_skip_does_not_fabricate_missing_requirements_either():
    """The skip must not be modelled by pretending its requirements are uncovered —
    that would be the same fallback in reverse. Coverage reflects only what was read;
    the skip is reported alongside it."""
    catalog = [_clause("4.1", "clause")]
    failed = uuid.uuid4()
    report = coverage_report(
        _FakeSession([catalog[0].id]), run=_run([uuid.uuid4(), failed], [_skip(failed)]), clauses=catalog
    )

    assert report["clauses"]["covered"] == 1
    assert report["clauses"]["missing_codes"] == []
    assert report["skipped_documents"]


# --- fix 3: run duration is measurable --------------------------------------


def test_completed_at_uses_the_wall_clock_not_the_transaction_clock():
    """PostgreSQL's now() returns the time the TRANSACTION began, so it reported a
    27-second run as 0.05s — the field meant to answer "how long did this take"
    measured nothing. clock_timestamp() is the real clock."""
    import inspect

    from app.tasks import run_gap_analysis

    source = inspect.getsource(run_gap_analysis._now)
    assert "clock_timestamp" in source
    assert "func.now()" not in source


# --- each document must be committed as it completes ------------------------


def test_each_document_is_committed_as_it_completes():
    """A rollback for document N must not discard documents 1..N-1.

    record_mappings only calls add(), so with a single commit deferred to the end of
    the loop, rolling back a late failure also threw away every earlier document's
    pending rows — turning one failed call back into a lost run, which is the exact
    thing per-document isolation exists to prevent. Caught by running a two-document
    set with the failure on the second one.
    """
    import inspect

    from app.tasks import run_gap_analysis

    source = inspect.getsource(run_gap_analysis.start_run)
    body = source[source.index("for document in documents:") :]
    commit_inside_try = body.index("db.commit()")
    rollback = body.index("db.rollback()")

    assert commit_inside_try < rollback, (
        "the per-document commit must come before the except/rollback, so each "
        "document is durable on its own"
    )
