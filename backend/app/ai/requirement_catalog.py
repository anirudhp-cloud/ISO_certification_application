# Formats the seeded requirement catalog (app/models/clause.py rows) into the
# text block injected into a map-step system prompt (app/ai/openai_client.py)
# — so the LLM evaluates documents against THIS app's actual catalog data
# (title, description, evidence requirements) instead of relying on whatever
# it happens to remember about the standard from training.
#
# One segment per call: the clause pass gets the 32 mandatory clauses, the control
# pass gets the 38 Annex A controls with their Annex B guidance. Splitting costs
# almost nothing — the catalogue splits along with the prompt — and it keeps ~15
# lines of Annex B instruction out of the clause prompt, where it never applied.
#
# Current size (o200k, measured): clause 5,306 + control 9,741 = 15,047 tokens, of
# which 4,173 is the obligation lists added below.

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
        # The mark scheme — and the reason the prompt can ask for one verdict per
        # numbered obligation. Omitting it was a real defect: the prompt instructed
        # the model to return {"index": n, "verdict": ...} against a list it had
        # never been shown, so it invented indices. Across 668 stored mappings EVERY
        # one answered index 0, and 544 answered nothing else — the model was giving
        # a single holistic verdict and labelling it 0, which is exactly the vague
        # judgement the obligations were introduced to replace.
        if c.obligations:
            entry += "\n  Obligations (judge each one separately, return its index):\n" + "\n".join(
                f"    [{i}] {text}" for i, text in enumerate(c.obligations)
            )
        # Annex B guidance exists only for Annex A controls; clause rows carry NULL.
        # Skipped outright for the clause segment so the clause prompt never has to
        # explain a field it will never see.
        if segment == "control" and c.implementation_guidance:
            entry += "\n  Implementation guidance (Annex B — check each point against the document):\n" + "\n".join(
                f"    - {point}" for point in c.implementation_guidance
            )
        lines.append(entry)
    return "\n".join(lines)
