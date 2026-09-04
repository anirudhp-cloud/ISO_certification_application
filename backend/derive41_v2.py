# Clause 4.1, re-derived with the NOTES attached where they belong.
#
# The first attempt flattened all three NOTEs into one 15-line list at the END of the
# requirement, after the obligations. Two things went wrong with that:
#
#   - The six role lines exist only to define obligation [3] and the eight context
#     lines only to define [0], but presented as one flat list the model got 15 aids
#     and 4 obligations with no mapping between them. Judging [3] ("the
#     organization's role(s) are determined") it had no binding indication that
#     "role" means AI provider / producer / customer, and quoted the document's
#     internal job-title table instead.
#   - Only the NOTES' list items were kept and every prose sentence dropped —
#     including "The organization's roles can determine the applicability and extent
#     of applicability of the requirements and controls in this document", which is
#     the most consequential sentence in 4.1's notes.
#
# So: `look_for` hangs off each obligation, `note` carries the standard's own prose,
# and where an enumeration DEFINES an obligation rather than merely helping locate it
# (roles, in [3]) it moves into the obligation text itself — the model must not be
# able to read "role" as "job title".

CLAUSE_41 = {
    "code": "4.1",
    "title": "Understanding the organization and its context",
    "documented_information_required": False,  # 4.1 says "determine"/"consider" only
    "requirements": [
        {
            "text": "External and internal issues relevant to the organization's purpose, "
                    "that affect its ability to achieve the intended result(s) of the AI "
                    "management system, are determined",
            "actor": "organization",
            "evidence_kind": "determination",
            "look_for": [
                "external: applicable legal requirements, including prohibited uses of AI",
                "external: policies, guidelines and decisions from regulators that affect "
                "the interpretation or enforcement of legal requirements",
                "external: incentives or consequences associated with the intended purpose "
                "and use of AI systems",
                "external: culture, traditions, values, norms and ethics with respect to "
                "development and use of AI",
                "external: competitive landscape and trends for new products and services "
                "using AI systems",
                "internal: organizational context, governance, objectives, policies and procedures",
                "internal: contractual obligations",
                "internal: intended purpose of the AI system to be developed or used",
            ],
            "note": "External and internal issues to be addressed under this clause vary "
                    "according to the organization's roles and jurisdiction, and their impact "
                    "on its ability to achieve the intended outcome(s) of the AIMS.",
        },
        {
            "text": "Whether climate change is a relevant issue has been determined",
            "actor": "organization",
            "evidence_kind": "determination",
            "look_for": [
                "an explicit determination that climate change is, or is not, a relevant "
                "issue for this organization",
            ],
            "note": None,
        },
        {
            "text": "The intended purpose of the AI system(s) that are developed, provided or "
                    "used by the organization is considered",
            "actor": "organization",
            "evidence_kind": "determination",
            "look_for": [
                "a statement of what the organization's AI system(s) are for",
                "whether each system is developed, provided, or used by the organization",
            ],
            "note": None,
        },
        {
            # The enumeration is IN the obligation text, not the hints: it is what the
            # word "role" MEANS here, and the previous run proved the model will
            # otherwise read it as an internal job title.
            "text": "The organization's role(s) with respect to those AI systems are "
                    "determined — that is, whether it acts as an AI provider, AI producer, "
                    "AI customer, AI partner, AI subject, or relevant authority",
            "actor": "organization",
            "evidence_kind": "determination",
            "look_for": [
                "AI provider: AI platform providers, AI product or service providers",
                "AI producer: AI developers, designers, operators, testers and evaluators, "
                "deployers, human factor professionals, domain experts, impact assessors, "
                "procurers, governance and oversight professionals",
                "AI customer: including AI users",
                "AI partner: AI system integrators, data providers",
                "AI subject: data subjects and other subjects",
                "relevant authorities: policymakers and regulators",
                "the role may follow from the categories of data processed (e.g. PII "
                "controller or PII processor), or from legal requirements specific to AI systems",
            ],
            "note": "The organization's roles can determine the applicability and extent of "
                    "applicability of the requirements and controls in this document. Detailed "
                    "role descriptions are given in ISO/IEC 22989; the relationship of roles to "
                    "the AI system life cycle is also described in the NIST AI risk management "
                    "framework.",
        },
    ],
}


def render(requirement: dict) -> str:
    """The requirement block appended to the system prompt.

    Each obligation prints its own index, actor, evidence kind, search aids and, where
    the standard has one, the NOTE prose that bears on it. Nothing floats free of the
    obligation it belongs to.
    """
    lines = [
        f"CLAUSE {requirement['code']} — {requirement['title']}",
        "",
        f"This clause {'requires' if requirement['documented_information_required'] else 'does NOT require'} "
        f"documented information."
        + ("" if requirement["documented_information_required"] else
           " It says 'determine' and 'consider'. Evidence may therefore sit in any"
           " record showing the determination was made — it need not be a dedicated document."),
        "",
        "REQUIREMENTS TO BE SATISFIED — judge each one separately and return a verdict for each:",
    ]
    for index, requirement_item in enumerate(requirement["requirements"]):
        lines += [
            "",
            f"  [{index}] {requirement_item['text']}",
            f"       who must do it: {requirement_item['actor']}",
            f"       satisfied by:   {requirement_item['evidence_kind']}",
        ]
        if requirement_item.get("look_for"):
            lines.append("       look for (informative, from the standard's NOTES — these carry")
            lines.append("       no verdict of their own and cannot make this requirement unmet):")
            lines += [f"         · {aid}" for aid in requirement_item["look_for"]]
        if requirement_item.get("note"):
            lines.append(f"       NOTE: {requirement_item['note']}")
    return "\n".join(lines)
