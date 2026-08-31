# M3 tests: the per-document clause/control response shape.
#
# The interesting behaviour isn't the happy path — it's the three states a document
# can be in. Two of them show no requirements, and they mean opposite things to
# whoever uploaded the file:
#   not_analysed — nobody has run Analyze yet
#   no_match     — it WAS read, in full, and supports nothing (misfiled document,
#                  wrong standard tag, or extraction produced no text)
# Collapsing those into one empty list is the gap that left developers with no
# feedback at all, so each is pinned here.

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.evidence_mapping import DocumentMappingsRead, RequirementMappingRead, SegmentMappingsRead


def _requirement(code="A.2.2", *, location="Section \"4. AI Principles\", paragraph 1", unmet=None, total=12):
    return RequirementMappingRead(
        code=code,
        title="AI policy",
        category="A.2 Policies related to AI",
        relevance_score=95.0,
        coverage_score=75.0,
        rationale="All AI activities shall be guided by the following core principles.",
        source_location=location,
        unmet_guidance_points=unmet or [],
        guidance_points_total=total,
    )


def _response(status, *, clauses=None, controls=None, run_id=None):
    return DocumentMappingsRead(
        document_id=uuid.uuid4(),
        document_name="AI Policy document",
        file_name="2A.AI_Policy for TechVest.docx",
        version_number=1,
        certification_standard="iso42001",
        status=status,
        run_id=run_id,
        analysed_at=None,
        clauses=SegmentMappingsRead(
            segment="clause", matched=len(clauses or []), total=32, mappings=clauses or []
        ),
        controls=SegmentMappingsRead(
            segment="control", matched=len(controls or []), total=38, mappings=controls or []
        ),
    )


def test_segments_report_matched_against_the_standards_own_totals():
    """"3 of 32" must come from the catalogue, not a hardcoded number — the totals
    differ per standard (ISO 9001 has no controls at all)."""
    response = _response("matched", clauses=[_requirement("5.2", total=0)], controls=[_requirement()])
    assert (response.clauses.matched, response.clauses.total) == (1, 32)
    assert (response.controls.matched, response.controls.total) == (1, 38)


def test_not_analysed_carries_no_run():
    response = _response("not_analysed")
    assert response.run_id is None
    assert response.clauses.mappings == [] and response.controls.mappings == []


def test_no_match_carries_the_run_that_read_it():
    """This is what separates it from not_analysed: a run exists and read the
    document, it just found nothing."""
    run = uuid.uuid4()
    response = _response("no_match", run_id=run)
    assert response.status == "no_match"
    assert response.run_id == run
    assert response.clauses.mappings == [] and response.controls.mappings == []


def test_clause_requirements_carry_no_guidance_points():
    """Clauses 4-10 have no Annex B, so guidance is always empty for that segment —
    guidance_points_total of 0 lets the UI omit the section entirely rather than
    rendering '0 of 0 not satisfied'."""
    clause = _requirement("5.2", total=0)
    assert clause.guidance_points_total == 0
    assert clause.unmet_guidance_points == []


def test_unmet_guidance_is_reported_against_the_controls_total():
    control = _requirement(unmet=["The AI policy should be informed by business strategy."], total=12)
    assert len(control.unmet_guidance_points) == 1
    assert control.guidance_points_total == 12


def test_missing_citation_is_representable():
    """OCR'd documents produce no positional chunks, so the quote can't be located.
    That must be expressible rather than blocking the response."""
    control = _requirement(location=None)
    assert control.source_location is None
    assert control.rationale  # the quote itself survives


def test_status_is_required():
    """Without it, 'read and matched nothing' is indistinguishable from
    'never analysed' — the whole point of the field."""
    with pytest.raises(ValidationError):
        DocumentMappingsRead(
            document_id=uuid.uuid4(),
            document_name="d",
            file_name="d.docx",
            version_number=1,
            certification_standard="iso42001",
            run_id=None,
            analysed_at=None,
            clauses=SegmentMappingsRead(segment="clause", matched=0, total=32, mappings=[]),
            controls=SegmentMappingsRead(segment="control", matched=0, total=38, mappings=[]),
        )
