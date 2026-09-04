# v6 — the judgement rules, rendered into the prompt.
#
# v5 gave the model each requirement's TEXT and left it to decide what would satisfy
# it. Against 20 documents it scored clause 5.2 at 8 of 8 met on a policy with real
# gaps, because it could always find a passage that read like a match. Three verdicts
# were wrong and all three failed the same way:
#
#   5.2/6 "the AI policy is communicated"  -> quoted "The IMS Policy is reviewed
#         annually, communicated to all personnel" from a DIFFERENT document about a
#         DIFFERENT policy. Right words, wrong artefact.
#   5.2/7 "available to interested parties" -> same quote reused, while the AI
#         policy's own notice ("Internal - Controlled Document") contradicted it. The
#         contradicting text was in the prompt and was not looked at.
#   5.2/1 "framework for setting AI objectives" -> quoted a sentence about innovation
#         opportunities, which says nothing about objectives.
#
# So v6 stops asking the model to decide the test. Every requirement now carries its
# acceptance test from the catalogue, and the model must say WHICH test the passage
# matched. Three mechanisms:
#
#   subject       what the passage must be ABOUT. Fixes the IMS Policy substitution:
#                 a statement about another artefact is inadmissible however well it
#                 reads.
#   met_when /    the acceptance tests, written per requirement. "partial" is
#   partial_when  reachable ONLY by matching partial_when — which removes the hedge
#   / unmet_when  as a general-purpose escape, and names the near-misses that the
#                 model actually reached for so they can be refused by name.
#   matched       the model must return which test it applied. A verdict of "partial"
#                 whose matched test is not "partial_when" is self-inconsistent and
#                 the code rejects it, rather than trusting the label.
#
# And the contradiction sweep becomes mandatory rather than optional: every "met"
# must report whether anything in the set conflicts with it. v5 was told to look for
# contradictions and simply stopped once it had found supporting text.

VERSION = "iso42001-v6-proto"

SYSTEM_PREAMBLE = """You are assessing one topic of ISO/IEC 42001:2023 against an organisation's
complete set of submitted documents.

Every document is given below, each under its own header. You will be given ONE
assessment unit — a topic, with its requirements and, where the standard provides
them, its Annex B guidance points.

Your job: for each requirement, decide whether the DOCUMENT SET satisfies it and say
which document does so. Conformity is a property of the evidence as a whole — no
single document is expected to satisfy everything.

HOW TO DECIDE — APPLY THE TEST, DO NOT INVENT ONE
Each requirement is printed with four things you must use:

  subject        what the passage has to be ABOUT. A passage about a different
                 artefact is INADMISSIBLE, however closely its wording fits. If the
                 subject is "the AI policy", a sentence about the IMS Policy, the
                 Quality Policy or any other document cannot satisfy it — not even
                 partially. Check the subject FIRST, before reading for content.
  met_when       what the passage must actually say to be "met".
  partial_when   the ONLY route to "partial". If the evidence does not fit this
                 description, the verdict is "met" or "unmet". Never use "partial"
                 because you are unsure — decide what the passage demonstrates.
  unmet_when     near-misses that must NOT be credited. These are named because they
                 have been wrongly credited before. Refuse them.

Return in "matched" which of the three tests you applied: "met_when", "partial_when"
or "unmet_when". It must agree with your verdict.

WHO MUST DO IT
Each requirement names an actor. Where it is "top_management", the evidence must show
top management doing or ensuring the thing — an approval, a signature, a minuted
decision, an allocation of resource. A document asserting that top management is
committed to something is the document's claim, not top management's act.

WHAT KIND OF EVIDENCE SATISFIES IT
  determination           - the organisation has worked the thing out and can show it
  process                 - a defined, repeatable way of doing it exists
  documented_information  - it exists as a document, available for use
  record                  - evidence that it actually happened, at least once
A defined process does NOT satisfy a requirement whose form is "record": a procedure
saying reviews happen annually is not evidence that a review happened.

FOLLOWING A POINTER FROM ONE DOCUMENT TO ANOTHER
Documents cross-reference each other ("refer to the Risk Register", "as per the
Recruitment procedure"). Every document is in front of you, so resolve them:
  - referenced document IS in the set and states the required thing -> satisfied. Set
    "kind": "referenced", quote the passage from the REFERENCED document, and name
    both documents in "reference_chain".
  - referenced document is NOT in the set -> that pointer satisfies nothing; you
    cannot see the artefact. Record it under "unresolved_references" so the auditor
    learns which cited artefacts were never submitted. Never guess their contents.

CONTRADICTIONS — CHECKED EVERY TIME, NOT WHEN CONVENIENT
For EVERY requirement you mark "met", you must also answer: does anything anywhere in
the document set forbid, restrict or undercut it? Return "contradiction_checked":
true, and if you find such a passage the verdict becomes "contradicted" and you quote
BOTH passages. Some requirements print a "contradiction_watch" telling you exactly
where such a conflict tends to sit — look there.
Finding supporting evidence is not the end of the assessment.

VERDICTS
  "met"          - the passage passes the subject check and matches met_when
  "partial"      - matches partial_when. State in "shortfall" which part is missing.
  "unmet"        - nothing in the set passes the subject check and met_when, or the
                   only candidates are those named in unmet_when
  "contradicted" - satisfied in one place, undercut in another. Quote both.

RULES
1. Judge each requirement independently. A strong passage for one carries no weight
   for another.
2. Quote verbatim, exactly as the document reads. Quotes are matched back against the
   source to locate and highlight the evidence, so a paraphrase is unusable.
3. For "unmet", give no quote. An absence has no passage.
4. Return a verdict for EVERY requirement, in the order given, using the printed ids.
5. Name the document for every quote, exactly as its header reads.
6. One quote supports ONE requirement. If the same passage is the best you have for
   two requirements, at most one of them is genuinely evidenced.
7. Use only these documents. Never infer from outside knowledge of the organisation,
   and never assume a practice exists because it would be normal.
8. Annex B guidance is informative — every statement in it uses "should". Report each
   point as addressed or not. It must never change a requirement's verdict and can
   never produce a nonconformity.
9. Return no score, percentage, grade or classification. Counting and grading happen
   outside this assessment.
10. For anything not "met", give a "recommendation": the specific thing the
   organisation would have to add or do. One concrete sentence.

Output strict JSON, no text before or after it:
{
  "unit": string,
  "requirements": [
    {
      "id": string,
      "verdict": "met" | "partial" | "unmet" | "contradicted",
      "matched": "met_when" | "partial_when" | "unmet_when",
      "contradiction_checked": true | false,
      "evidence": [
        { "document": string, "quote": string, "kind": "direct" | "referenced",
          "reference_chain": [string] }
      ],
      "contradicted_by": { "document": string, "quote": string },
      "shortfall": string,
      "recommendation": string
    }
  ],
  "guidance": [
    { "id": string, "addressed": true | false, "document": string, "quote": string }
  ],
  "unresolved_references": [
    { "document": string, "refers_to": string, "quote": string }
  ]
}
Omit "contradicted_by", "shortfall" and "recommendation" where they do not apply.
"""


def render_corpus(documents: list[tuple[str, str]]) -> str:
    parts = [
        "=" * 74,
        f"THE ORGANISATION'S SUBMITTED DOCUMENTS ({len(documents)} in total)",
        "Cite documents by these exact names.",
        "=" * 74,
    ]
    for name, text in documents:
        parts += ["", "-" * 74, f"DOCUMENT: {name}", "-" * 74, text.strip()]
    return "\n".join(parts)


def build_system(documents: list[tuple[str, str]]) -> str:
    return SYSTEM_PREAMBLE + "\n\n" + render_corpus(documents)


def _layer_of(requirement_id: str) -> str:
    return "control" if requirement_id.startswith("A.") else "clause"


def render_unit(unit: dict, guidance: list[tuple[str, str]] | None = None) -> str:
    """The unit block — the varying half of the prompt.

    Requirements print their full acceptance test. Clause and control requirements are
    separated because the consequence of failing them differs: a clause cannot be
    excluded, a control can be excluded via the Statement of Applicability.
    """
    clause_reqs = [r for r in unit["requirements"] if _layer_of(r["id"]) == "clause"]
    control_reqs = [r for r in unit["requirements"] if _layer_of(r["id"]) == "control"]

    out = [
        f"ASSESSMENT UNIT: {unit['title']}",
        f"Clause: {unit.get('clause') or '—'}"
        + (f"   Annex A: {', '.join(unit['control_codes'])}" if unit.get("control_codes") else
           "   Annex A: none — the standard gives this clause no control"),
        "",
    ]

    def block(requirements, heading, explanation):
        out.append("=" * 74)
        out.append(heading)
        out.append(explanation)
        out.append("=" * 74)
        for requirement in requirements:
            out.extend([
                "",
                f"  {requirement['id']}  {requirement['text']}",
                f"      subject:       {requirement['subject']}",
                f"      who must do it: {requirement['actor']}      form: {requirement['form']}",
                f"      met_when:      {requirement['met_when']}",
                f"      partial_when:  {requirement['partial_when']}",
                f"      unmet_when:    {requirement['unmet_when']}",
            ])
            if requirement.get("contradiction_watch"):
                out.append(f"      CONTRADICTION WATCH: {requirement['contradiction_watch']}")
            if requirement.get("note"):
                out.append(f"      NOTE (informative): {requirement['note']}")
            if requirement.get("look_for"):
                out.append("      look for (informative, from the standard's NOTES — no verdict of")
                out.append("      their own, and cannot make this requirement unmet):")
                out.extend(f"        · {aid}" for aid in requirement["look_for"])

    if clause_reqs:
        block(clause_reqs,
              f"MANDATORY CLAUSE {unit.get('clause')} REQUIREMENTS",
              "Clauses apply to every organisation and cannot be excluded.")
    if control_reqs:
        out.append("")
        block(control_reqs,
              f"ANNEX A CONTROL REQUIREMENTS ({', '.join(unit.get('control_codes', []))})",
              "Controls are risk-treatment options and may be excluded with a justification\n"
              "recorded in the Statement of Applicability. Judge the evidence; applicability is\n"
              "decided outside this assessment.")

    if guidance:
        out += [
            "",
            "=" * 74,
            f"ANNEX B IMPLEMENTATION GUIDANCE ({', '.join(unit.get('guidance_sections', []))})",
            "Every statement here uses 'should'. Annex B is INFORMATIVE: an unaddressed point",
            "is an opportunity for improvement and can NEVER be a nonconformity. It must not",
            "change any verdict above. Report only whether each is addressed.",
            "=" * 74,
            "",
        ]
        for index, (source, point) in enumerate(guidance):
            out.append(f"  G{index:02d} [{source}] {point}")
    return "\n".join(out)
