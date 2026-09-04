# Tests for obligation-based scoring and the computed rollup.
#
# What these pin down is that the score is ARITHMETIC, not a judgement. Under the
# previous design the model returned a coverage percentage directly, and across 1,057
# real mappings only 30 distinct values appeared out of 101 with 98% a multiple of 5 —
# the signature of a number chosen from a mental menu. Worse, one document evidencing
# 1 of clause 7.5.2's 3 obligations was scored 100%, because a single vague question
# invites a single confident answer and hides what is missing.
#
# The regression test for all of that is test_one_of_three_obligations_is_not_full_
# coverage below.

from types import SimpleNamespace

import pytest

from app.ai.grading import CONFORMING, MAJOR_NC, MINOR_NC, NOT_APPLICABLE, OFI
from app.ai.grading import propose_grade_from_obligations as grade
from app.ai.rollup import combined_unmet_guidance, roll_up_obligations
from app.ai.schemas import ClauseEvaluation, ObligationVerdict
from app.ai.scoring import (
    compute_coverage,
    format_fraction,
    is_mapped,
    normalise_evaluation,
    obligation_counts,
    partial_count,
)


def _v(index, verdict, quote="q"):
    return ObligationVerdict(index=index, verdict=verdict, quote=quote if verdict != "unmet" else None)


# --- the arithmetic --------------------------------------------------------


def test_one_of_three_obligations_is_not_full_coverage():
    """The exact case the old design got wrong. A real document evidencing only
    clause 7.5.2's first obligation — via a DOCUMENT CONTROL table — was scored 100%.
    It is 1 of 3."""
    verdicts = [_v(0, "met"), _v(1, "unmet"), _v(2, "unmet")]

    assert format_fraction(verdicts, 3) == "1 of 3"
    assert compute_coverage(verdicts, 3) == pytest.approx(33.33, abs=0.01)


def test_a_partial_does_not_count_toward_the_satisfied_count():
    """Half-credit was tried and abandoned. It produced "0.5 of 3" — meaningless for
    documentation, since half an obligation is not something an auditor can record —
    and it flattered the evidence, because "partly documented" is not "documented".
    Partials are reported separately instead."""
    verdicts = [_v(0, "met"), _v(1, "partial"), _v(2, "unmet")]

    assert format_fraction(verdicts, 3) == "1 of 3"
    assert partial_count(verdicts) == 1
    # Still orderable above a requirement with no partial at all, for sorting only.
    assert compute_coverage(verdicts, 3) > compute_coverage([_v(0, "met")], 3)


def test_the_shown_count_is_always_a_whole_number():
    for verdicts in (
        [_v(0, "partial")],
        [_v(0, "partial"), _v(1, "partial")],
        [_v(0, "met"), _v(1, "partial")],
    ):
        assert "." not in format_fraction(verdicts, 3)


def test_partials_alone_satisfy_nothing():
    verdicts = [_v(0, "partial"), _v(1, "partial"), _v(2, "partial")]
    assert format_fraction(verdicts, 3) == "0 of 3"
    assert partial_count(verdicts) == 3


def test_all_obligations_met_is_full_coverage():
    verdicts = [_v(0, "met"), _v(1, "met")]
    assert format_fraction(verdicts, 2) == "2 of 2"
    assert compute_coverage(verdicts, 2) == 100.0


def test_coverage_divides_by_the_requirements_total_not_the_answers_given():
    """Otherwise a model returning only the obligations it liked would score 100% by
    omission. Two answers against a three-obligation requirement is 2 of 3."""
    verdicts = [_v(0, "met"), _v(1, "met")]
    assert compute_coverage(verdicts, 3) == pytest.approx(66.67, abs=0.01)
    assert format_fraction(verdicts, 3) == "2 of 3"


def test_a_requirement_with_no_mark_scheme_scores_zero_rather_than_full():
    assert compute_coverage([_v(0, "met")], 0) == 0.0


def test_counts_are_reported_per_verdict():
    verdicts = [_v(0, "met"), _v(1, "met"), _v(2, "partial"), _v(3, "unmet")]
    assert obligation_counts(verdicts) == {"met": 2, "partial": 1, "unmet": 1}


# --- normalising what the model returned -----------------------------------


def test_an_index_past_the_end_of_the_mark_scheme_earns_no_credit():
    """`index` is free text on the wire like any other field. An index past the end of
    the obligation list would otherwise score against an obligation that doesn't
    exist."""
    evaluation = ClauseEvaluation(
        requirement_code="7.5.2", obligations=[_v(0, "met"), _v(9, "met")]
    )
    normalise_evaluation(evaluation, 3)

    assert [v.index for v in evaluation.obligations] == [0]
    assert evaluation.coverage_score == pytest.approx(33.33, abs=0.01)


def test_a_negative_index_is_rejected_at_the_schema_boundary():
    """Caught by the schema rather than needing the scoring pass to filter it."""
    with pytest.raises(Exception):
        ObligationVerdict(index=-1, verdict="met", quote="q")


def test_a_repeated_index_keeps_the_strongest_answer_and_is_not_double_counted():
    evaluation = ClauseEvaluation(
        requirement_code="7.5.2", obligations=[_v(0, "partial"), _v(0, "met"), _v(1, "unmet")]
    )
    normalise_evaluation(evaluation, 2)

    assert len(evaluation.obligations) == 2
    assert evaluation.obligations[0].verdict == "met"
    assert format_fraction(evaluation.obligations, 2) == "1 of 2"


def test_the_summary_quote_comes_from_the_strongest_verdict():
    evaluation = ClauseEvaluation(
        requirement_code="7.5.2",
        obligations=[_v(1, "partial", "weaker passage"), _v(0, "met", "stronger passage")],
    )
    normalise_evaluation(evaluation, 3)
    assert evaluation.rationale == "stronger passage"


def test_the_model_cannot_set_the_score():
    """A coverage_score arriving on the wire is overwritten by the computed value —
    otherwise the model could bypass the arithmetic entirely."""
    evaluation = ClauseEvaluation(
        requirement_code="7.5.2", coverage_score=100.0, obligations=[_v(0, "met"), _v(1, "unmet")]
    )
    normalise_evaluation(evaluation, 2)
    assert evaluation.coverage_score == 50.0  # 1 of 2 met, no partials


def test_a_partial_still_beats_unmet_when_deduping():
    """Strength and credit are different orderings: a partial earns no credit but is a
    stronger answer than unmet, so it must win the tie."""
    evaluation = ClauseEvaluation(
        requirement_code="7.5.2", obligations=[_v(0, "unmet"), _v(0, "partial")]
    )
    normalise_evaluation(evaluation, 1)
    assert evaluation.obligations[0].verdict == "partial"


# --- mapping is derived, not asked -----------------------------------------


def test_a_document_maps_only_if_it_satisfies_an_obligation():
    """This retires the separate relevance_score the model used to guess alongside
    the coverage score."""
    assert is_mapped(ClauseEvaluation(requirement_code="5.2", obligations=[_v(0, "met")]))
    assert is_mapped(ClauseEvaluation(requirement_code="5.2", obligations=[_v(0, "partial")]))
    assert not is_mapped(
        ClauseEvaluation(requirement_code="5.2", obligations=[_v(0, "unmet"), _v(1, "unmet")])
    )
    assert not is_mapped(ClauseEvaluation(requirement_code="5.2", obligations=[]))


# --- the rollup across documents (replacing the reduce LLM call) -----------


def _mapping(doc_name, verdicts, unmet_guidance=None):
    return SimpleNamespace(
        document_id=doc_name,
        document=SimpleNamespace(document_name=doc_name),
        obligation_verdicts=verdicts,
        unmet_guidance_points=unmet_guidance,
        coverage_score=0,
    )


def test_the_rollup_takes_the_strongest_verdict_per_obligation_across_documents():
    """Evidence split across documents jointly satisfies a requirement — one document
    covering obligation 1 and another covering obligation 2 is 2 of 2."""
    obligations = ["first", "second"]
    mappings = [
        _mapping("A.docx", [{"index": 0, "verdict": "met", "quote": "a"}]),
        _mapping("B.docx", [{"index": 1, "verdict": "met", "quote": "b"}]),
    ]
    rolled = roll_up_obligations(obligations, mappings)

    assert rolled["fraction"] == "2 of 2"
    assert rolled["met"] == 2
    assert rolled["unmet_obligations"] == []


def test_the_rollup_names_the_obligations_no_document_satisfies():
    """The audit question. The prose narrative this replaced buried it in a
    paragraph."""
    obligations = ["identification", "format and media", "review and approval"]
    mappings = [_mapping("A.docx", [{"index": 0, "verdict": "met", "quote": "a"}])]
    rolled = roll_up_obligations(obligations, mappings)

    assert rolled["fraction"] == "1 of 3"
    assert rolled["unmet_obligations"] == ["format and media", "review and approval"]


def test_the_rollup_records_which_documents_support_each_obligation():
    obligations = ["first"]
    mappings = [
        _mapping("A.docx", [{"index": 0, "verdict": "partial", "quote": "weak"}]),
        _mapping("B.docx", [{"index": 0, "verdict": "met", "quote": "strong"}]),
    ]
    rolled = roll_up_obligations(obligations, mappings)
    first = rolled["obligations"][0]

    assert first["verdict"] == "met"
    assert first["document_count"] == 2
    # Strongest first, so "strongest: <document>" means something.
    assert first["documents"][0]["document_name"] == "B.docx"


def test_an_obligation_absent_from_every_document_is_unmet_not_unknown():
    rolled = roll_up_obligations(["first", "second"], [_mapping("A.docx", [])])
    assert [o["verdict"] for o in rolled["obligations"]] == ["unmet", "unmet"]
    assert rolled["fraction"] == "0 of 2"


# --- Annex B stays guidance, separate from the obligations -----------------


def test_unmet_annex_b_is_the_intersection_across_documents():
    """A guidance point one document leaves unaddressed can be covered by another, so
    only points EVERY document leaves unaddressed remain unmet."""
    mappings = [
        _mapping("A.docx", [], unmet_guidance=["p1", "p2"]),
        _mapping("B.docx", [], unmet_guidance=["p2", "p3"]),
    ]
    assert combined_unmet_guidance(mappings) == ["p2"]


def test_unmet_annex_b_with_a_single_document_is_that_documents_list():
    assert combined_unmet_guidance([_mapping("A.docx", [], unmet_guidance=["p1"])]) == ["p1"]


# --- grading from counts, with no thresholds -------------------------------


@pytest.mark.parametrize(
    "segment,total,met,partial,guidance,expected",
    [
        ("clause", 3, 3, 0, None, CONFORMING),
        ("clause", 3, 2, 1, None, MINOR_NC),
        ("clause", 3, 2, 0, None, MINOR_NC),
        ("clause", 3, 1, 0, None, MAJOR_NC),
        ("clause", 3, 0, 0, None, MAJOR_NC),
        ("control", 2, 2, 0, None, CONFORMING),
        ("control", 2, 2, 0, ["p"], OFI),
        ("control", 2, 1, 0, None, MINOR_NC),
        ("control", 2, 0, 0, None, MINOR_NC),
    ],
)
def test_the_grade_follows_from_the_counts(segment, total, met, partial, guidance, expected):
    assert (
        grade(
            segment=segment,
            total_obligations=total,
            met=met,
            partial=partial,
            unmet_guidance_points=guidance,
        )
        == expected
    )


def test_no_control_ever_grades_major_regardless_of_the_counts():
    """Severity of a control gap depends on the risk it treats, and there is no risk
    register here — calling it major would invent severity."""
    for met in range(0, 4):
        for partial in range(0, 4 - met):
            assert (
                grade(
                    segment="control",
                    total_obligations=3,
                    met=met,
                    partial=partial,
                    unmet_guidance_points=None,
                )
                != MAJOR_NC
            )


def test_an_excluded_control_grades_not_applicable():
    assert (
        grade(
            segment="control",
            total_obligations=2,
            met=0,
            partial=0,
            unmet_guidance_points=None,
            is_applicable=False,
        )
        == NOT_APPLICABLE
    )


def test_a_requirement_with_no_mark_scheme_does_not_imply_an_assessment():
    """Nothing can be counted, so it must not read as conforming."""
    assert (
        grade(segment="clause", total_obligations=0, met=0, partial=0, unmet_guidance_points=None)
        == MAJOR_NC
    )


# --- highlight-all: every satisfying passage in one document -----------------
#
# Answering "where is this quote" one citation at a time is not how an auditor reads
# a file. These cover the multi-passage path: labelling, deduplication, and the fact
# that an unlocatable quote is reported rather than dropped.


def test_satisfying_passages_skips_unmet_and_quoteless_verdicts():
    """An unmet obligation has no passage — it must contribute no highlight rather
    than an approximate one."""
    from app.api.routes.documents import _satisfying_passages

    class _Clause:
        code = "7.2"

    class _Mapping:
        clause = _Clause()
        obligation_verdicts = [
            {"index": 0, "verdict": "met", "quote": "competence is determined",
             "obligation": "competence determined"},
            {"index": 1, "verdict": "unmet", "quote": None, "obligation": "persons competent"},
            {"index": 2, "verdict": "partial", "quote": "", "obligation": "actions taken"},
        ]

    import app.api.routes.documents as routes

    original = routes.list_for_document
    routes.list_for_document = lambda db, **kw: [_Mapping()]
    try:
        passages = _satisfying_passages(None, "doc-id")
    finally:
        routes.list_for_document = original

    assert len(passages) == 1
    assert passages[0]["quote"] == "competence is determined"
    assert passages[0]["label"].startswith("7.2 (met)")


def test_one_passage_evidencing_two_requirements_is_highlighted_once():
    """The same sentence can legitimately satisfy obligations under two requirements.
    Highlighting it twice just doubles the annotation, so the labels merge instead."""
    from app.api.routes.documents import _satisfying_passages
    import app.api.routes.documents as routes

    def _mapping(code):
        clause = type("C", (), {"code": code})()
        return type("M", (), {
            "clause": clause,
            "obligation_verdicts": [
                {"index": 0, "verdict": "met", "quote": "shared sentence",
                 "obligation": f"obligation of {code}"}
            ],
        })()

    original = routes.list_for_document
    routes.list_for_document = lambda db, **kw: [_mapping("5.2"), _mapping("A.2.2")]
    try:
        passages = _satisfying_passages(None, "doc-id")
    finally:
        routes.list_for_document = original

    assert len(passages) == 1
    assert "5.2 (met)" in passages[0]["label"]
    assert "A.2.2 (met)" in passages[0]["label"]
