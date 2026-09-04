# v5 — requirement-first. Every document in front of the model at once; one
# assessment unit per call.
#
# WHY THE LOOP IS INVERTED
# v3 asks "which of the 70 requirements does THIS document satisfy?", once per
# document. Three things follow from that shape and none of them are fixable by
# rewording the prompt:
#
#   - one call judges 123 requirements, which is where the hedging and the wrong
#     indices came from;
#   - clause 5.2 and control A.2.2 are both about the AI policy, and the standard
#     says so, but they are judged in different calls that never meet;
#   - a pointer from one document to another is unresolvable. Judging document 25
#     alone, "Refer to the Recruitment procedure" cannot be checked — so today it is
#     discarded, even though that procedure IS in the set and does state the thing.
#     Measured on the real set: 14 of 35 documents point at another artefact, 11 of
#     those references resolve to a submitted document and 12 do not.
#
# v5 asks "who satisfies THIS unit?" over the whole corpus. 54 units, so 54 calls per
# run regardless of how many documents were uploaded.
#
# WHY THERE IS NO SEARCH INDEX
# The whole corpus is ~87,000 tokens — under 10% of the context window. There is no
# haystack to index. The corpus goes in the SYSTEM message so it is the static
# cacheable prefix; the unit goes in the USER message. That is the inversion of what
# is cached today, where the catalogue was static and the document varied.

VERSION = "iso42001-v5-proto"

SYSTEM_PREAMBLE = """You are assessing one topic of ISO/IEC 42001:2023 against an organisation's
complete set of submitted documents.

Every document is given below, each under its own header. You will be given ONE
assessment unit — a topic, with the mandatory clause requirements, the Annex A control
requirements, and the Annex B guidance points that the standard groups under it.

Your job is to say, for each requirement, whether the DOCUMENT SET satisfies it and
which document does so. Conformity is a property of the evidence as a whole, not of any
single document: no one document is expected to satisfy everything.

WHAT COUNTS AS EVIDENCE
A passage evidences a requirement when it states, about the organisation, the thing the
requirement demands — specifically enough that a reader could tell whether it had been
done. It follows that these are NOT evidence:
  - a passage that names the topic without stating what the organisation does about it
  - a document's own control block (id, version, classification, prepared/reviewed/
    approved-by), which shows how that one file is controlled and nothing more
  - a heading, title, purpose statement or scope sentence, unless it itself states the
    required thing
  - a passage about an adjacent subject. Sustainability is not climate change; a table
    of internal job titles is not a determination of the organisation's role as an AI
    provider or customer. Adjacent is "unmet", not "partial".

FOLLOWING A POINTER FROM ONE DOCUMENT TO ANOTHER
Documents cross-reference each other ("refer to the Risk Register", "as per the
Recruitment procedure"). Because every document is in front of you, resolve them:
  - if the referenced document IS in the set and states the required thing, the
    requirement is satisfied. Set "kind": "referenced", quote the passage from the
    REFERENCED document, and name both documents in "reference_chain".
  - if the referenced document is NOT in the set, the requirement is NOT satisfied by
    that pointer — you cannot see the artefact. Record it in
    "unresolved_references" so the auditor learns which cited artefacts were never
    submitted. Do not guess at their contents.

CONTRADICTIONS
If one passage satisfies a requirement while another passage in the set forbids or
undercuts it, the verdict is "contradicted", and you must quote BOTH. Example: a policy
that must be "available to interested parties" while its own notice marks it internal
use only, reproduction prohibited. A contradiction is not a partial — it is a defect
that a reader of the document set would hit.

WHO MUST DO IT
Each requirement names its actor. Where the actor is "top_management", evidence must
show top management doing or ensuring it — an approval, a signature, a minuted
decision, an allocation. A document asserting that top management is committed to
something is the document's claim, not top management's act.

WHAT KIND OF EVIDENCE SATISFIES IT
  determination           - the organisation has worked the thing out and can show it
  process                 - a defined, repeatable way of doing it exists
  documented_information  - it exists as a document, available for use
  record                  - evidence that it actually happened, at least once
A defined process does NOT satisfy a requirement whose kind is "record": a procedure
saying reviews happen annually is not evidence that a review happened.

VERDICTS
  "met"          - a passage states the required thing, by the required actor, in the
                   required form. Quote it.
  "partial"      - this requirement is addressed incompletely: part of what it demands
                   is evidenced and part is not, or an intention is stated rather than a
                   practice. Say in "shortfall" exactly which part is missing. A
                   "partial" with no stated shortfall is not acceptable — if you cannot
                   name what is missing, the verdict is "met" or "unmet".
  "unmet"        - nothing in the set addresses this requirement
  "contradicted" - satisfied in one place and undercut in another; quote both

RULES
1. Judge each requirement independently. A strong passage for one carries no weight
   for another.
2. Quote verbatim, exactly as the document reads. Quotes are matched back against the
   source to locate and highlight the evidence, so a paraphrase is unusable.
3. For "unmet", give no quote. An absence has no passage.
4. Return a verdict for EVERY requirement listed, in the order given, using the ids
   exactly as printed.
5. Name the document for every quote, exactly as its header reads.
6. Use only these documents. Never infer from outside knowledge of the organisation
   and never assume a practice exists because it would be normal.
7. Annex B guidance is informative. Report each point as addressed or not; it must
   never change a Layer 1 or Layer 2 verdict, and never produces a nonconformity.
8. Return no score, percentage, grade or classification. Counting and grading happen
   outside this assessment.
9. Where a requirement is not satisfied, give a "recommendation": the specific thing
   the organisation would have to add or do. One sentence, concrete.

Output strict JSON, no text before or after it:
{
  "unit": string,
  "requirements": [
    {
      "id": string,
      "verdict": "met" | "partial" | "unmet" | "contradicted",
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
    """Every document under its own header, as the static cacheable prefix.

    Named headers matter: the model has to cite documents by name, and it needs to be
    able to navigate 87,000 tokens by name rather than by position.
    """
    parts = [
        "=" * 74,
        f"THE ORGANISATION'S SUBMITTED DOCUMENTS ({len(documents)} in total)",
        "Each document appears once, under a header giving its name. Cite documents by",
        "these exact names.",
        "=" * 74,
    ]
    for name, text in documents:
        parts += ["", "-" * 74, f"DOCUMENT: {name}", "-" * 74, text.strip()]
    return "\n".join(parts)


def build_system(documents: list[tuple[str, str]]) -> str:
    return SYSTEM_PREAMBLE + "\n\n" + render_corpus(documents)
