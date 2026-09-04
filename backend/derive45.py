# Clauses 4 and 5, re-derived from the transcribed standard (iso_text/page_013..016).
#
# One obligation per separately-evidenceable printed duty: every lettered or dashed
# item is its own obligation, and a compound verb list inside one sentence splits only
# where the evidence differs. The previous catalogue was derived from a prose summary,
# which collapsed exactly the nested lists the standard uses to state separate duties.
#
# Two fields are new:
#   actor         - "organization" or "top_management", as the standard names it. The
#                   evidence bar differs: a policy existing says nothing about whether
#                   TOP MANAGEMENT ensured the resources were available.
#   evidence_kind - determination / process / documented_information / record. This is
#                   what makes 6.1.2 ("define a risk assessment process") and 8.2
#                   ("perform assessments, retain the results") distinguishable.
#
# `hints` are NOTE-derived. NOTEs in ISO are informative, so they can never produce a
# nonconformity - they tell the model what to search for. Clause-side twin of Annex B.

import json
import pathlib

DERIVED = {
    "4.1": {
        "title": "Understanding the organization and its context",
        "obligations": [
            {"text": "External and internal issues relevant to the organization's purpose, that affect its ability to achieve the intended result(s) of the AIMS, are determined",
             "actor": "organization", "evidence_kind": "determination"},
            {"text": "Whether climate change is a relevant issue has been determined",
             "actor": "organization", "evidence_kind": "determination"},
            {"text": "The intended purpose of the AI system(s) developed, provided or used by the organization is considered",
             "actor": "organization", "evidence_kind": "determination"},
            {"text": "The organization's role(s) with respect to those AI systems are determined",
             "actor": "organization", "evidence_kind": "determination"},
        ],
        "hints": [
            "Roles: AI provider (AI platform providers, AI product or service providers)",
            "Roles: AI producer (developers, designers, operators, testers and evaluators, deployers, human factor professionals, domain experts, impact assessors, procurers, governance and oversight professionals)",
            "Roles: AI customer (including AI users)",
            "Roles: AI partner (system integrators, data providers)",
            "Roles: AI subject (data subjects and other subjects)",
            "Roles: relevant authorities (policymakers, regulators)",
            "Role can follow from the data categories processed (e.g. PII controller or PII processor)",
            "External context: applicable legal requirements, including prohibited uses of AI",
            "External context: policies, guidelines and decisions from regulators affecting interpretation or enforcement",
            "External context: incentives or consequences associated with the intended purpose and use of AI systems",
            "External context: culture, traditions, values, norms and ethics regarding development and use of AI",
            "External context: competitive landscape and trends for new products and services using AI",
            "Internal context: organizational context, governance, objectives, policies and procedures",
            "Internal context: contractual obligations",
            "Internal context: intended purpose of the AI system to be developed or used",
        ],
    },
    "4.2": {
        "title": "Understanding the needs and expectations of interested parties",
        "obligations": [
            {"text": "The interested parties relevant to the AIMS are determined",
             "actor": "organization", "evidence_kind": "determination"},
            {"text": "The relevant requirements of those interested parties are determined",
             "actor": "organization", "evidence_kind": "determination"},
            {"text": "Which of those requirements will be addressed through the AIMS is determined",
             "actor": "organization", "evidence_kind": "determination"},
        ],
        "hints": ["Interested parties can have requirements related to climate change"],
    },
    "4.3": {
        "title": "Determining the scope of the AI management system",
        "obligations": [
            {"text": "The boundaries and applicability of the AIMS are determined, establishing its scope",
             "actor": "organization", "evidence_kind": "determination"},
            {"text": "In determining the scope, the external and internal issues referred to in 4.1 are considered",
             "actor": "organization", "evidence_kind": "determination"},
            {"text": "In determining the scope, the interested-party requirements referred to in 4.2 are considered",
             "actor": "organization", "evidence_kind": "determination"},
            {"text": "The scope is available as documented information",
             "actor": "organization", "evidence_kind": "documented_information"},
            {"text": "The scope determines the organization's activities with respect to this document's requirements on the AIMS, leadership, planning, support, operation, performance evaluation, improvement, controls and objectives",
             "actor": "organization", "evidence_kind": "determination"},
        ],
        "hints": [],
    },
    "4.4": {
        "title": "AI management system",
        "obligations": [
            {"text": "An AI management system is established, implemented and maintained in accordance with the requirements of this document",
             "actor": "organization", "evidence_kind": "process"},
            {"text": "The AI management system is continually improved",
             "actor": "organization", "evidence_kind": "record"},
            {"text": "The AI management system is documented, including the processes needed and their interactions",
             "actor": "organization", "evidence_kind": "documented_information"},
        ],
        "hints": [],
    },
    "5.1": {
        "title": "Leadership and commitment",
        "obligations": [
            {"text": "Top management ensures the AI policy and AI objectives are established and are compatible with the strategic direction of the organization",
             "actor": "top_management", "evidence_kind": "determination"},
            {"text": "Top management ensures the integration of the AIMS requirements into the organization's business processes",
             "actor": "top_management", "evidence_kind": "determination"},
            {"text": "Top management ensures the resources needed for the AIMS are available",
             "actor": "top_management", "evidence_kind": "determination"},
            {"text": "Top management communicates the importance of effective AI management and of conforming to the AIMS requirements",
             "actor": "top_management", "evidence_kind": "record"},
            {"text": "Top management ensures the AIMS achieves its intended result(s)",
             "actor": "top_management", "evidence_kind": "record"},
            {"text": "Top management directs and supports persons to contribute to the effectiveness of the AIMS",
             "actor": "top_management", "evidence_kind": "record"},
            {"text": "Top management promotes continual improvement",
             "actor": "top_management", "evidence_kind": "record"},
            {"text": "Top management supports other relevant roles to demonstrate their leadership as it applies to their areas of responsibility",
             "actor": "top_management", "evidence_kind": "record"},
        ],
        "hints": [
            "Business can be interpreted broadly as the activities core to the organization's purpose",
            "Establishing, encouraging and modelling a culture of responsible AI use, development and governance can be an important demonstration of top-management commitment",
        ],
    },
    "5.2": {
        "title": "AI policy",
        "obligations": [
            {"text": "An AI policy is established that is appropriate to the purpose of the organization",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"text": "The AI policy provides a framework for setting AI objectives",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"text": "The AI policy includes a commitment to meet applicable requirements",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"text": "The AI policy includes a commitment to continual improvement of the AIMS",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"text": "The AI policy is available as documented information",
             "actor": "organization", "evidence_kind": "documented_information"},
            {"text": "The AI policy refers, as relevant, to other organizational policies",
             "actor": "organization", "evidence_kind": "documented_information"},
            {"text": "The AI policy is communicated within the organization",
             "actor": "organization", "evidence_kind": "record"},
            {"text": "The AI policy is available to interested parties, as appropriate",
             "actor": "organization", "evidence_kind": "record"},
        ],
        "hints": ["Considerations for organizations developing AI policies are provided in ISO/IEC 38507"],
    },
    "5.3": {
        "title": "Roles, responsibilities and authorities",
        "obligations": [
            {"text": "Top management ensures the responsibilities and authorities for relevant roles are assigned and communicated within the organization",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"text": "Responsibility and authority for ensuring the AIMS conforms to the requirements of this document is assigned",
             "actor": "top_management", "evidence_kind": "documented_information"},
            {"text": "Responsibility and authority for reporting on the performance of the AIMS to top management is assigned",
             "actor": "top_management", "evidence_kind": "documented_information"},
        ],
        "hints": ["Control A.3.2 covers defining and allocating AI roles and responsibilities; guidance in B.3.2"],
    },
}

if __name__ == "__main__":
    pathlib.Path("catalog_draft_45.json").write_text(
        json.dumps(DERIVED, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    seed = json.load(open("../seed_data/iso42001_requirements.json", encoding="utf-8"))
    old = {r["code"]: r["obligations"] for r in seed["requirements"]}

    print(f"{'code':7} {'was':>4} {'now':>4} {'hints':>6}   title")
    was = now = 0
    for code, entry in DERIVED.items():
        o, n = len(old.get(code, [])), len(entry["obligations"])
        was += o
        now += n
        print(f"{code:7} {o:>4} {n:>4} {len(entry['hints']):>6}   {entry['title']}")
    print(f"{'TOTAL':7} {was:>4} {now:>4}")
