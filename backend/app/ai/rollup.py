# Requirement-level rollup: many documents' obligation verdicts folded into one
# assessment per requirement — computed, with no LLM call.
#
# This replaces the reduce step. That step asked the model to merge several documents'
# results into a prose narrative, which produced text like:
#
#   "Identification/description, format/media, and review/approval for suitability and
#    adequacy are demonstrated as follows: Standard document control template ... is
#    explicitly mandated by 26.Documented_Information_Control_Procedure ("Documents
#    must follow a standard template...")."
#
# Three problems with that. It is prose ABOUT documents rather than a quote FROM one,
# so it cannot be located — on a real run 11 of 50 multi-document findings had no
# resolvable citation. It buried the actual audit question (which obligation does
# NOBODY evidence?) inside a paragraph. And it cost a further ~70 API calls and ~$0.45
# per run to produce.
#
# With obligation verdicts there is nothing to merge in prose: take the strongest
# verdict per obligation across all contributing documents, and the answer falls out —
# including, crucially, the obligations no document satisfies at all.

from app.ai.scoring import (
    VERDICT_STRENGTH,
    compute_coverage,
    format_fraction,
    partial_count,
)


def _rank(verdict: str) -> int:
    """met > partial > unmet. Strength, not credit — a partial earns no credit toward
    the count but is still a stronger answer than nothing at all."""
    return VERDICT_STRENGTH.get(verdict, 0)


def roll_up_obligations(obligations: list[str], mappings: list) -> dict:
    """Fold every contributing document's verdicts into one view of the requirement.

    `mappings` are EvidenceMapping rows for one clause in one run. Returns, per
    obligation, the best verdict any document achieved and which document achieved it,
    so an auditor sees both what is covered and by what.
    """
    per_obligation = []
    for index, text in enumerate(obligations):
        best = None
        supporting = []
        for mapping in mappings:
            for verdict in mapping.obligation_verdicts or []:
                if verdict.get("index") != index:
                    continue
                if verdict.get("verdict") in ("met", "partial"):
                    supporting.append((mapping, verdict))
                if best is None or _rank(verdict.get("verdict", "")) > _rank(best[1].get("verdict", "")):
                    best = (mapping, verdict)

        # Strongest evidence first, so "strongest: <document>" is meaningful.
        supporting.sort(key=lambda pair: _rank(pair[1].get("verdict", "")), reverse=True)
        verdict_value = best[1].get("verdict") if best else "unmet"
        per_obligation.append(
            {
                "index": index,
                "obligation": text,
                # An obligation absent from every document's verdicts is unmet, not
                # unknown: the model is asked to return a verdict for every obligation
                # of any requirement it includes.
                "verdict": verdict_value,
                "document_count": len({m.document_id for m, _ in supporting}),
                "documents": [
                    {
                        "document_id": str(m.document_id),
                        "document_name": m.document.document_name,
                        "verdict": v.get("verdict"),
                        "quote": v.get("quote"),
                        "source_location": v.get("source_location"),
                    }
                    for m, v in supporting
                ],
            }
        )

    verdicts = [{"verdict": o["verdict"]} for o in per_obligation]
    total = len(obligations)
    return {
        "obligations": per_obligation,
        "total_obligations": total,
        "coverage_score": compute_coverage(verdicts, total),
        # How the score is written for a person — "2 of 3", never a percentage.
        "fraction": format_fraction(verdicts, total),
        "met": sum(1 for o in per_obligation if o["verdict"] == "met"),
        # Reported alongside the count, never folded into it. "Partly documented" is
        # not "documented", and half an obligation is not something an auditor records.
        "partial": partial_count(verdicts),
        "partial_obligations": [o["obligation"] for o in per_obligation if o["verdict"] == "partial"],
        # The audit question: which obligations does no document evidence?
        "unmet_obligations": [o["obligation"] for o in per_obligation if o["verdict"] == "unmet"],
    }


def combined_unmet_guidance(mappings: list) -> list[str]:
    """Annex B points no contributing document addresses.

    A point one document leaves unaddressed can still be covered by another, so this
    is the intersection of what every document left unmet — not the union. Kept apart
    from the obligations because Annex B is guidance: an unaddressed point is an
    opportunity for improvement, never a shortfall against the control.
    """
    per_document = [set(m.unmet_guidance_points or []) for m in mappings]
    if not per_document:
        return []
    still_unmet = set.intersection(*per_document) if len(per_document) > 1 else per_document[0]
    return sorted(still_unmet)
