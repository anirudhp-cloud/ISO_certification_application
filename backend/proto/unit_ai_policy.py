# One ASSESSMENT UNIT: everything ISO/IEC 42001 says about the AI policy.
#
# Clause 5.2 says so itself — "Control objectives and controls for establishing an AI
# policy are provided in A.2 in Table A.1. Implementation guidance for these controls
# is provided in B.2." The current architecture ignores that pointer: clause 5.2 is
# judged in one call and A.2.2 in a different one, so nothing ever assesses "the AI
# policy" as a whole. Grouping them is the standard's instruction, not an invention.
#
# The three layers stay separately gradable even though they are assessed together,
# because the consequence of failing each is different:
#
#   clause requirement unmet   -> nonconformity. Clauses cannot be excluded.
#   control requirement unmet  -> nonconformity ONLY if the control is applicable
#                                 per the Statement of Applicability.
#   Annex B point unaddressed  -> opportunity for improvement. NEVER a nonconformity,
#                                 because every verb in Annex B is "should".
#
# Requirements come from the standard's printed wording (see iso_text/), one per
# separately-evidenceable duty. Annex B points are verbatim from the catalogue.

UNIT = {
    "id": "ai_policy",
    "title": "AI policy",
    "sources": ["5.2", "A.2.2", "A.2.3", "A.2.4", "B.2.2", "B.2.3", "B.2.4"],
    # ---- Layer 1: mandatory clause requirements -------------------------------
    "clause": {
        "code": "5.2",
        "title": "AI policy",
        "requirements": [
            {"id": "5.2/0", "text": "An AI policy is established that is appropriate to the purpose of the organization",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"id": "5.2/1", "text": "The AI policy provides a framework for setting AI objectives (see 6.2)",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"id": "5.2/2", "text": "The AI policy includes a commitment to meet applicable requirements",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"id": "5.2/3", "text": "The AI policy includes a commitment to continual improvement of the AI management system",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"id": "5.2/4", "text": "The AI policy is available as documented information",
             "actor": "organization", "evidence_kind": "documented_information"},
            {"id": "5.2/5", "text": "The AI policy refers, as relevant, to other organizational policies",
             "actor": "organization", "evidence_kind": "documented_information"},
            {"id": "5.2/6", "text": "The AI policy is communicated within the organization",
             "actor": "organization", "evidence_kind": "record"},
            {"id": "5.2/7", "text": "The AI policy is available to interested parties, as appropriate",
             "actor": "organization", "evidence_kind": "record"},
        ],
        "note": "Considerations for organizations when developing AI policies are provided in ISO/IEC 38507.",
    },
    # ---- Layer 2: Annex A controls (excludable via the SoA) -------------------
    "controls": [
        {"code": "A.2.2", "title": "AI policy",
         "statement": "The organization shall document a policy for the development or use of AI systems.",
         "requirements": [
             {"id": "A.2.2/0", "text": "A policy for the development or use of AI systems is documented",
              "actor": "organization", "evidence_kind": "documented_information"},
         ]},
        {"code": "A.2.3", "title": "Alignment with other organizational policies",
         "statement": "The organization shall determine where other policies can be affected by, or apply to, "
                      "the organization's objectives with respect to AI systems.",
         "requirements": [
             {"id": "A.2.3/0", "text": "Other policies that can be affected by, or apply to, the organization's "
                                       "objectives with respect to AI systems are determined",
              "actor": "organization", "evidence_kind": "determination"},
             {"id": "A.2.3/1", "text": "The relationship between the AI policy and those other policies is addressed",
              "actor": "organization", "evidence_kind": "documented_information"},
         ]},
        {"code": "A.2.4", "title": "Review of the AI policy",
         "statement": "The AI policy shall be reviewed at planned intervals or additionally as needed to ensure "
                      "its continuing suitability, adequacy and effectiveness.",
         "requirements": [
             {"id": "A.2.4/0", "text": "The AI policy is reviewed at planned intervals, and additionally as needed",
              "actor": "organization", "evidence_kind": "process"},
             {"id": "A.2.4/1", "text": "The review addresses the policy's continuing suitability, adequacy and effectiveness",
              "actor": "organization", "evidence_kind": "record"},
         ]},
    ],
    # ---- Layer 3: Annex B guidance (informative — OFI at most) ----------------
    "guidance": [
        ("B.2.2", "The AI policy should be informed by business strategy."),
        ("B.2.2", "The AI policy should be informed by organizational values and culture and the amount of risk the organization is willing to pursue or retain."),
        ("B.2.2", "The AI policy should be informed by the level of risk posed by the AI systems."),
        ("B.2.2", "The AI policy should be informed by legal requirements, including contracts."),
        ("B.2.2", "The AI policy should be informed by the risk environment of the organization."),
        ("B.2.2", "The AI policy should be informed by impact to relevant interested parties."),
        ("B.2.2", "The AI policy should include principles that guide all activities of the organization related to AI."),
        ("B.2.2", "The AI policy should include processes for handling deviations and exceptions to policy."),
        ("B.2.2", "The AI policy should consider topic-specific aspects such as AI resources and assets."),
        ("B.2.2", "The AI policy should consider topic-specific aspects such as AI system impact assessments."),
        ("B.2.2", "The AI policy should consider topic-specific aspects such as AI system development."),
        ("B.2.2", "Relevant policies should guide the development, purchase, operation and use of AI systems."),
        ("B.2.3", "The organization should analyse whether and where current policies (e.g. quality, security, safety, privacy) intersect with AI."),
        ("B.2.3", "The organization should update those existing policies if updates are required, or include provisions in the AI policy."),
        ("B.2.4", "A role approved by management should be responsible for the development, review and evaluation of the AI policy or its components."),
        ("B.2.4", "The review should assess opportunities for improvement in response to changes to the organizational environment, business circumstances, legal conditions or technical environment."),
        ("B.2.4", "The review of the AI policy should take the results of management reviews into account."),
    ],
}


def render_unit(unit: dict) -> str:
    """The unit block — the only part of the prompt that changes between calls.

    Sent as the USER message, because the corpus is the static cacheable prefix and
    sits in the system message. That is the inversion: today the catalogue is cached
    and the document varies; here the documents are cached and the requirement varies.
    """
    out = [
        f"ASSESSMENT UNIT: {unit['title']}",
        f"Sources in the standard: {', '.join(unit['sources'])}",
        "",
        "This unit gathers everything ISO/IEC 42001 says about this topic. The three",
        "layers below are graded differently — keep them separate in your answer.",
        "",
        "=" * 74,
        f"LAYER 1 — MANDATORY CLAUSE {unit['clause']['code']} ({unit['clause']['title']})",
        "Clauses apply to every organisation and cannot be excluded. A requirement here",
        "that no document satisfies is a shortfall against the standard.",
        "=" * 74,
    ]
    for requirement in unit["clause"]["requirements"]:
        out += [
            "",
            f"  {requirement['id']}  {requirement['text']}",
            f"        who must do it: {requirement['actor']}   satisfied by: {requirement['evidence_kind']}",
        ]
    if unit["clause"].get("note"):
        out += ["", f"  NOTE (informative): {unit['clause']['note']}"]

    out += [
        "",
        "=" * 74,
        "LAYER 2 — ANNEX A CONTROLS",
        "Controls are risk-treatment options. They are selected from the organisation's",
        "AI risk assessment and may be EXCLUDED with a justification recorded in the",
        "Statement of Applicability. Judge them on the evidence; whether an excluded",
        "control still counts is decided outside this assessment.",
        "=" * 74,
    ]
    for control in unit["controls"]:
        out += ["", f"  {control['code']} — {control['title']}", f"        control text: {control['statement']}"]
        for requirement in control["requirements"]:
            out += [
                f"    {requirement['id']}  {requirement['text']}",
                f"        who must do it: {requirement['actor']}   satisfied by: {requirement['evidence_kind']}",
            ]

    out += [
        "",
        "=" * 74,
        "LAYER 3 — ANNEX B IMPLEMENTATION GUIDANCE",
        "Every statement here uses 'should'. Annex B is INFORMATIVE: an unaddressed point",
        "is an opportunity for improvement and can NEVER be a nonconformity. It must not",
        "change any verdict in Layer 1 or Layer 2. Report only whether each is addressed.",
        "=" * 74,
        "",
    ]
    for index, (source, point) in enumerate(unit["guidance"]):
        out.append(f"  G{index:02d} [{source}] {point}")
    return "\n".join(out)
