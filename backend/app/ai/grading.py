# Proposed grades — what a certification body actually issues, replacing the
# invented `>=70 met / >=30 partial / else gap` rubric in crud/finding.py.
#
# ISO auditors don't grade in percentages. They issue conformity, an opportunity for
# improvement, a minor nonconformity or a major nonconformity — and a major NC blocks
# certification while an OFI does not. Those consequences are not expressible as
# met/partial/gap, and 70 and 30 were numbers with no basis in the standard.
#
# Everything here produces a SUGGESTION. The auditor's decision lives in
# findings.grade; this only fills findings.proposed_grade. The tool reads documents —
# it cannot sample records, interview staff or observe practice, so its output is a
# documentary review and must be labelled as one.

from app.config import settings

CONFORMING = "conforming"
OFI = "ofi"
MINOR_NC = "minor_nc"
MAJOR_NC = "major_nc"
NOT_APPLICABLE = "not_applicable"

# Evidence states, derived rather than stored. The distinction the old status column
# could not make: a requirement nobody has submitted evidence for looked identical to
# one that was examined and found wanting — the two most consequential states to tell
# apart in a Stage 1 review.
NO_EVIDENCE = "no_evidence"
INSUFFICIENT = "insufficient"
SATISFIED = "satisfied"

GRADE_LABELS = {
    CONFORMING: "Conforming",
    OFI: "Opportunity for improvement",
    MINOR_NC: "Minor nonconformity",
    MAJOR_NC: "Major nonconformity",
    NOT_APPLICABLE: "Not applicable",
}


def evidence_state(*, has_evidence: bool, coverage_score: float | None) -> str:
    if not has_evidence:
        return NO_EVIDENCE
    if coverage_score is not None and coverage_score >= settings.grade_full_coverage_threshold:
        return SATISFIED
    return INSUFFICIENT


def propose_grade_from_obligations(
    *,
    segment: str,
    total_obligations: int,
    met: int,
    partial: int,
    unmet_guidance_points: list[str] | None,
    is_applicable: bool | None = None,
) -> str:
    """Grade from a COUNT of obligations — no thresholds.

    The percentage thresholds this replaces (90 and 50) were numbers I chose, acting
    on a coverage figure the model had also chosen. Two layers of invention stacked on
    each other: a finding at 89% proposed minor_nc and one at 90% proposed conforming,
    and the difference between them was sampling noise.

    Counting removes both. Either every obligation is satisfied or it is not, and the
    only remaining judgement — whether unaddressed Annex B guidance is an OFI rather
    than a shortfall — follows from Annex B being guidance, not a requirement.
    """
    if segment == "control" and is_applicable is False:
        return NOT_APPLICABLE

    if total_obligations <= 0:
        # No mark scheme seeded for this requirement; nothing can be counted, so
        # refuse to imply an assessment happened.
        return MAJOR_NC if segment == "clause" else MINOR_NC

    if met == 0 and partial == 0:
        return MAJOR_NC if segment == "clause" else MINOR_NC

    if met == total_obligations:
        # Every obligation satisfied. Unaddressed Annex B guidance is worth improving,
        # not a failure to meet the control.
        return OFI if unmet_guidance_points else CONFORMING

    # Some but not all. A mandatory clause with nothing evidenced is already handled
    # above; a clause still missing obligations is a shortfall against a requirement
    # no organisation may exclude, so it grades harder than a control gap whose
    # severity would depend on a risk register that does not exist here.
    if segment == "clause" and (met + partial) * 2 <= total_obligations:
        return MAJOR_NC
    return MINOR_NC


def propose_grade(
    *,
    segment: str,
    has_evidence: bool,
    coverage_score: float | None,
    unmet_guidance_points: list[str] | None,
    is_applicable: bool | None = None,
) -> str:
    """Legacy percentage-threshold grading, kept only for findings written before the
    mark scheme existed. New assessments use propose_grade_from_obligations.

    `segment` matters because the two halves of the standard carry different weight.
    A mandatory clause with no documented evidence is a candidate major
    nonconformity — the standard requires that documented information to exist. An
    Annex A control with no evidence is capped at minor: the severity of a control
    gap depends on the risk it was selected to treat, and there is no risk register
    here, so claiming major would be inventing severity the tool cannot judge.
    """
    if segment == "control" and is_applicable is False:
        return NOT_APPLICABLE

    if not has_evidence:
        return MAJOR_NC if segment == "clause" else MINOR_NC

    coverage = coverage_score if coverage_score is not None else 0.0
    unmet = unmet_guidance_points or []

    if coverage >= settings.grade_full_coverage_threshold:
        # Fully covered on the requirement itself, but Annex B guidance points left
        # unaddressed are exactly what an OFI is for: worth improving, not a failure
        # to meet the requirement.
        return OFI if unmet else CONFORMING

    if coverage >= settings.grade_partial_coverage_threshold:
        return MINOR_NC

    return MAJOR_NC if segment == "clause" else MINOR_NC


def blocks_certification(grade: str | None) -> bool:
    """Only a major NC blocks a certificate. Used to summarise a report honestly
    instead of implying every gap is equally serious."""
    return grade == MAJOR_NC
