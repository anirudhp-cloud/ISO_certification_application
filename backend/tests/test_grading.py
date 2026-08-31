# M5 tests: the proposed-grade model that replaces the invented
# `>=70 met / >=30 partial / else gap` rubric.
#
# The behaviour worth pinning is the ASYMMETRY between the two segments. A mandatory
# clause with no documented evidence is a candidate major nonconformity — the standard
# requires that documented information to exist. An Annex A control with no evidence
# is capped at minor, because the severity of a control gap depends on the risk it was
# selected to treat and there is no risk register here; grading it major would invent
# severity the tool cannot judge.

import pytest

from app.ai.grading import (
    CONFORMING,
    INSUFFICIENT,
    MAJOR_NC,
    MINOR_NC,
    NO_EVIDENCE,
    NOT_APPLICABLE,
    OFI,
    SATISFIED,
    blocks_certification,
    evidence_state,
    propose_grade,
)


# --- evidence state: the distinction status could not make ------------------


def test_nothing_submitted_is_distinct_from_submitted_and_inadequate():
    assert evidence_state(has_evidence=False, coverage_score=None) == NO_EVIDENCE
    assert evidence_state(has_evidence=True, coverage_score=40.0) == INSUFFICIENT
    assert evidence_state(has_evidence=True, coverage_score=95.0) == SATISFIED


def test_evidence_with_no_score_counts_as_insufficient_not_satisfied():
    """Absent a score we must not assume the requirement is met."""
    assert evidence_state(has_evidence=True, coverage_score=None) == INSUFFICIENT


# --- the segment asymmetry -------------------------------------------------


def test_a_mandatory_clause_with_no_evidence_is_a_major_nc():
    assert propose_grade(
        segment="clause", has_evidence=False, coverage_score=None, unmet_guidance_points=None
    ) == MAJOR_NC


def test_a_control_with_no_evidence_is_capped_at_minor():
    """No risk register means no basis for calling a control gap major."""
    assert propose_grade(
        segment="control", has_evidence=False, coverage_score=None, unmet_guidance_points=None
    ) == MINOR_NC


def test_very_low_coverage_grades_harder_for_clauses_than_controls():
    kwargs = dict(has_evidence=True, coverage_score=10.0, unmet_guidance_points=None)
    assert propose_grade(segment="clause", **kwargs) == MAJOR_NC
    assert propose_grade(segment="control", **kwargs) == MINOR_NC


def test_no_control_ever_proposes_major_nc():
    for coverage in (0.0, 10.0, 49.9, 50.0, 89.9, 90.0, 100.0):
        grade = propose_grade(
            segment="control", has_evidence=True, coverage_score=coverage, unmet_guidance_points=None
        )
        assert grade != MAJOR_NC, f"coverage {coverage} proposed major NC for a control"


# --- the grade ladder ------------------------------------------------------


def test_full_coverage_with_all_guidance_met_is_conforming():
    assert propose_grade(
        segment="control", has_evidence=True, coverage_score=95.0, unmet_guidance_points=[]
    ) == CONFORMING


def test_full_coverage_with_unmet_guidance_is_an_ofi_not_a_nonconformity():
    """Annex B guidance left unaddressed is worth improving, not a failure to meet
    the requirement itself — which is exactly what an OFI is for."""
    assert propose_grade(
        segment="control",
        has_evidence=True,
        coverage_score=95.0,
        unmet_guidance_points=["The AI policy should be informed by business strategy."],
    ) == OFI


def test_partial_coverage_is_a_minor_nc_for_either_segment():
    for segment in ("clause", "control"):
        assert propose_grade(
            segment=segment, has_evidence=True, coverage_score=60.0, unmet_guidance_points=None
        ) == MINOR_NC


@pytest.mark.parametrize("coverage,expected", [(89.9, MINOR_NC), (90.0, CONFORMING)])
def test_the_full_coverage_threshold_is_inclusive(coverage, expected):
    assert propose_grade(
        segment="control", has_evidence=True, coverage_score=coverage, unmet_guidance_points=[]
    ) == expected


# --- applicability --------------------------------------------------------


def test_an_excluded_control_grades_not_applicable_regardless_of_coverage():
    assert propose_grade(
        segment="control",
        has_evidence=False,
        coverage_score=None,
        unmet_guidance_points=None,
        is_applicable=False,
    ) == NOT_APPLICABLE


def test_applicability_false_is_ignored_for_clauses():
    """Clauses can never be excluded, so even a stray False must not downgrade one."""
    assert propose_grade(
        segment="clause",
        has_evidence=False,
        coverage_score=None,
        unmet_guidance_points=None,
        is_applicable=False,
    ) == MAJOR_NC


# --- what actually blocks a certificate -----------------------------------


def test_only_a_major_nc_blocks_certification():
    assert blocks_certification(MAJOR_NC)
    for grade in (CONFORMING, OFI, MINOR_NC, NOT_APPLICABLE, None):
        assert not blocks_certification(grade)
