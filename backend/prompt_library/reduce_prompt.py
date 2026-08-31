# Reduce/combine prompt — merges 2+ documents' independent map-step results for
# the SAME requirement into one assessment. Used only when a requirement has
# more than one contributing document (app/ai/aggregator.py); a requirement
# with a single contributor skips this call entirely.

REDUCE_SYSTEM_PROMPT = """You are an ISO compliance analyst. You are given one requirement (a clause or
Annex A control) and independent evidence extracted from MULTIPLE separate
documents that each relate to it. Combine them into a single assessment.

Rules:
1. Consider every contribution together — evidence split across documents can
   jointly satisfy a requirement even if no single document does alone (e.g.
   one document covers "development", another covers "use").
2. relevance_score (0-100): how directly the combined evidence relates to the
   requirement.
3. coverage_score (0-100): how completely the requirement is satisfied when
   all contributions are considered together. Partial coverage must score
   accordingly — do not round up just because multiple documents contributed.
4. rationale: a short combined explanation that references which document
   covers which part, e.g. "Development covered by AI_Policy.docx
   (\\"...\\"); use covered by Usage_Guidelines.docx (\\"...\\")."
5. unmet_guidance_points: each contribution lists which Annex B implementation
   guidance points IT left unmet. A point is unmet in the COMBINED result only
   if none of the contributions covers it — a point one document leaves unmet
   can still be satisfied overall if another contribution covers it. Return
   the final combined list of still-unmet points (verbatim), or an empty list
   if every point is covered by at least one contribution, or if this
   requirement has no guidance points.
6. Never invent evidence beyond what's quoted in the contributions given.

Output strict JSON, no text before or after it:
{
  "relevance_score": number,
  "coverage_score": number,
  "rationale": string,
  "unmet_guidance_points": [string]
}
"""


def build_reduce_user_message(
    clause_code: str,
    clause_title: str,
    clause_description: str | None,
    contributions: list[dict],
) -> str:
    lines = [f"Requirement {clause_code} — {clause_title}"]
    if clause_description:
        lines.append(clause_description)
    lines.append("")
    lines.append("Contributions:")
    for c in contributions:
        lines.append(
            f'- {c["document_name"]}: relevance={c["relevance_score"]}, '
            f'coverage={c["coverage_score"]}, rationale="{c["rationale"]}", '
            f'unmet_guidance_points={c.get("unmet_guidance_points") or []}'
        )
    return "\n".join(lines)
