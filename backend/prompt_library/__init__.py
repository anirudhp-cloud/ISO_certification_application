"""System-prompt registry, keyed by (framework, segment).

A standard's requirements split into two segments that are not the same kind of
thing — mandatory clauses 4-10, and an excludable Annex A control catalogue with
Annex B guidance — so each gets its own prompt and its own LLM pass (see
app/ai/clause_mapper.py).

Not every standard has both: ISO 9001 has no Annex A at all, so it registers a
clause segment only. ISO 27001 has both but hasn't been split into separate prompts
yet — its single combined prompt is registered for both segments, which is harmless
because nothing exercises it until an ISO 27001 catalogue is seeded (only
seed_data/iso42001_requirements.json exists today). Callers must handle a segment
being absent, and app/ai/clause_mapper.py already skips any segment with no
requirements.
"""

from prompt_library import system_prompt_9k, system_prompt_27k, system_prompt_42k_clause, system_prompt_42k_control

CLAUSE = "clause"
CONTROL = "control"
SEGMENTS = (CLAUSE, CONTROL)

# (framework, segment) -> module exposing SYSTEM_PROMPT and VERSION
_PROMPTS = {
    ("ISO42001", CLAUSE): system_prompt_42k_clause,
    ("ISO42001", CONTROL): system_prompt_42k_control,
    ("ISO27001", CLAUSE): system_prompt_27k,
    ("ISO27001", CONTROL): system_prompt_27k,
    ("ISO9001", CLAUSE): system_prompt_9k,  # ISO 9001 has no Annex A control catalogue
}

# Frontend sends the standard id exactly as chosen on the "Select a Certification
# Standard" screen (see frontend/app.js `standards`) — lowercase, no separators.
STANDARD_ID_TO_FRAMEWORK = {
    "iso42001": "ISO42001",
    "iso27001": "ISO27001",
    "iso9001": "ISO9001",
}


def resolve_framework(standard_id: str) -> str:
    try:
        return STANDARD_ID_TO_FRAMEWORK[standard_id]
    except KeyError:
        raise ValueError(
            f"Unknown standard id '{standard_id}'. Expected one of: {', '.join(STANDARD_ID_TO_FRAMEWORK)}"
        )


def has_segment(standard_id: str, segment: str) -> bool:
    """Whether this standard defines the given segment at all — False for
    ('iso9001', 'control'), since ISO 9001 has no Annex A."""
    return (resolve_framework(standard_id), segment) in _PROMPTS


def get_system_prompt(standard_id: str, segment: str) -> tuple[str, str]:
    """Resolve a frontend standard id plus segment to (prompt text, prompt version).

    The version is recorded alongside results so findings produced under different
    prompt revisions stay distinguishable.
    """
    if segment not in SEGMENTS:
        raise ValueError(f"Unknown segment '{segment}'. Expected one of: {', '.join(SEGMENTS)}")

    framework = resolve_framework(standard_id)
    try:
        module = _PROMPTS[(framework, segment)]
    except KeyError:
        raise ValueError(f"{framework} has no '{segment}' segment — nothing to evaluate against")
    return module.SYSTEM_PROMPT, module.VERSION
