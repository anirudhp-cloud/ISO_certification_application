# Coverage arithmetic. The score is COUNTED from obligation verdicts here — the model
# never supplies one.
#
# Why: under the previous design the model returned a coverage percentage directly.
# Measured across 1,057 real mappings, only 30 distinct values appeared out of 101
# possible and 98% were a multiple of 5 — the signature of a number picked from a
# mental menu rather than derived. Worse, one document evidencing 1 of clause 7.5.2's
# 3 obligations was scored 100%, because a single vague question ("how well does this
# document satisfy 7.5.2?") invites a single confident answer and hides what is
# missing.
#
# Asking one narrow question per obligation removes that. The model answers
# met / partial / unmet with a quote; the fraction of obligations satisfied is then
# plain arithmetic, and every part of it traces to a passage in a document.
#
# The UI shows "n of m satisfied", not a percentage: with 3 obligations the only
# reachable values are 0, 1, 2 or 3 of 3, and rendering that as 0/33/67/100% implies a
# granularity that does not exist. coverage_score survives only as a sortable number
# and as the input to the grade rule.

from app.ai.schemas import ClauseEvaluation, ObligationVerdict

# An obligation is satisfied or it is not. A partial counts as NOT satisfied.
#
# Half-credit was tried and abandoned: it produced fractions like "0.5 of 3", which is
# meaningless for documentation — half an obligation is not a thing an auditor can
# record. It also flattered the evidence, since "partly documented" is not
# "documented". Partials are still tracked and shown, but as their own state alongside
# the count, never blended into it.
VERDICT_WEIGHTS = {"met": 1.0, "partial": 0.0, "unmet": 0.0}

# Kept separate so the strength of an assessment is still orderable: a requirement
# with two partials is weaker evidence than one with none, even though neither counts
# as satisfied.
PARTIAL_CREDIT_FOR_ORDERING = 0.25

# How strong one verdict is relative to another. Distinct from VERDICT_WEIGHTS, which
# is about credit: a partial earns no credit but is still a stronger answer than
# unmet, so "keep the strongest verdict" and "count what's satisfied" need different
# orderings. Collapsing them made a partial lose a tie against unmet.
VERDICT_STRENGTH = {"met": 2, "partial": 1, "unmet": 0}


def obligation_counts(verdicts: list[ObligationVerdict] | list[dict]) -> dict[str, int]:
    counts = {"met": 0, "partial": 0, "unmet": 0}
    for verdict in verdicts:
        value = verdict["verdict"] if isinstance(verdict, dict) else verdict.verdict
        if value in counts:
            counts[value] += 1
    return counts


def compute_coverage(verdicts: list[ObligationVerdict] | list[dict], total_obligations: int) -> float:
    """Fraction of this requirement's obligations satisfied, as a percentage.

    Divided by the requirement's TOTAL obligation count, not by the number the model
    answered — otherwise a model that returned only the obligations it liked would
    score 100% by omission. An obligation with no verdict counts as unmet.
    """
    if total_obligations <= 0:
        return 0.0
    counts = obligation_counts(verdicts)
    # Partials earn a small amount for ORDERING only — so a requirement with partial
    # evidence sorts above one with none — but they never count toward the "n of m"
    # shown to a person, and never make a requirement conforming.
    earned = counts["met"] + counts["partial"] * PARTIAL_CREDIT_FOR_ORDERING
    return round(min(earned, total_obligations) / total_obligations * 100, 2)


def satisfied_count(verdicts: list[ObligationVerdict] | list[dict]) -> int:
    """The "n" in "n of m satisfied" — a whole number, counting only fully satisfied
    obligations."""
    return obligation_counts(verdicts)["met"]


def format_fraction(verdicts: list[ObligationVerdict] | list[dict], total_obligations: int) -> str:
    """How the score is written for a person: "2 of 3".

    Always whole numbers. Partials are reported separately (see partial_count) rather
    than folded in as halves — "0.5 of 3" is not something an auditor can record, and
    counting half an obligation as satisfied overstates the evidence.
    """
    return f"{satisfied_count(verdicts)} of {total_obligations}"


def partial_count(verdicts: list[ObligationVerdict] | list[dict]) -> int:
    return obligation_counts(verdicts)["partial"]


def normalise_evaluation(
    evaluation: ClauseEvaluation, total_obligations: int
) -> ClauseEvaluation:
    """Fill in what the model must not decide: the score, and the summary quote.

    Also drops verdicts whose index falls outside the requirement's obligation list.
    `index` is free text on the wire like any other field, and an out-of-range index
    would otherwise silently earn credit against an obligation that does not exist.
    """
    in_range = [v for v in evaluation.obligations if 0 <= v.index < total_obligations]

    # One verdict per obligation. A repeated index would double-count; keep the
    # strongest answer for it, matching how duplicate requirement codes are handled.
    best: dict[int, ObligationVerdict] = {}
    for verdict in in_range:
        existing = best.get(verdict.index)
        if existing is None or VERDICT_STRENGTH.get(verdict.verdict, 0) > VERDICT_STRENGTH.get(
            existing.verdict, 0
        ):
            best[verdict.index] = verdict

    evaluation.obligations = [best[i] for i in sorted(best)]
    evaluation.coverage_score = compute_coverage(evaluation.obligations, total_obligations)

    # The document-level summary quote: the strongest verdict's passage. Used for the
    # citation lookup and the one-line preview, never as the justification on its own.
    quoted = [v for v in evaluation.obligations if v.quote and v.verdict in ("met", "partial")]
    if quoted:
        quoted.sort(key=lambda v: VERDICT_STRENGTH.get(v.verdict, 0), reverse=True)
        evaluation.rationale = quoted[0].quote
    return evaluation


def is_mapped(evaluation: ClauseEvaluation) -> bool:
    """Whether this document maps to the requirement at all.

    Derived, not asked. A document maps when it satisfies at least one obligation
    fully or partly — which retires the separate `relevance_score` the model used to
    guess alongside the coverage score.
    """
    return any(v.verdict in ("met", "partial") for v in evaluation.obligations)
