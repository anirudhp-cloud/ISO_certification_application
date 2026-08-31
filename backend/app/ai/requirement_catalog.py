# Formats the seeded requirement catalog (app/models/clause.py rows) into the
# text block injected into a map-step system prompt (app/ai/openai_client.py)
# — so the LLM evaluates documents against THIS app's actual catalog data
# (title, description, evidence requirements) instead of relying on whatever
# it happens to remember about the standard from training.
#
# One segment per call: the clause pass gets the 32 mandatory clauses, the control
# pass gets the 38 Annex A controls with their Annex B guidance. Splitting is
# effectively free — 3,472 + 10,884 tokens against 14,351 for the combined listing
# — and it keeps ~15 lines of Annex B instruction out of the clause prompt, where
# it never applied.

from app.models.clause import Clause

_HEADINGS = {
    "clause": "Full list of mandatory clauses for this standard (evaluate the document against every one of these):",
    "control": "Full list of Annex A controls for this standard (evaluate the document against every one of these):",
}


def split_by_segment(clauses: list[Clause]) -> dict[str, list[Clause]]:
    """Group a standard's catalog into {'clause': [...], 'control': [...]}, each in
    display order. A standard with no Annex A (ISO 9001) yields an empty control list,
    which callers skip rather than sending an empty catalog to the LLM."""
    grouped: dict[str, list[Clause]] = {"clause": [], "control": []}
    for clause in sorted(clauses, key=lambda c: c.sort_order):
        if clause.requirement_type in grouped:
            grouped[clause.requirement_type].append(clause)
    return grouped


def format_requirements_listing(clauses: list[Clause], segment: str) -> str:
    """Render one segment's catalog. `clauses` must already be filtered to `segment`
    (see split_by_segment)."""
    lines = [_HEADINGS.get(segment, "Full requirement list for this standard:")]
    for c in clauses:
        entry = f"- {c.code} ({c.requirement_type}) — {c.title}"
        if c.category:
            entry += f"\n  Category: {c.category}"
        if c.description:
            entry += f"\n  Description: {c.description}"
        if c.evidence_requirements:
            entry += f"\n  Evidence expected: {'; '.join(c.evidence_requirements)}"
        # Annex B guidance exists only for Annex A controls; clause rows carry NULL.
        # Skipped outright for the clause segment so the clause prompt never has to
        # explain a field it will never see.
        if segment == "control" and c.implementation_guidance:
            entry += "\n  Implementation guidance (Annex B — check each point against the document):\n" + "\n".join(
                f"    - {point}" for point in c.implementation_guidance
            )
        lines.append(entry)
    return "\n".join(lines)
