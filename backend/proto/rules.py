# JUDGEMENT RULES — the acceptance test for each requirement.
#
# WHY THESE EXIST
# The prototype scored clause 5.2 at 8 of 8 met, on a document a human reviewer found
# two nonconformities in. Three of the eight verdicts were wrong and all three failed
# the same way: the model was given a requirement's TEXT and left to decide what would
# satisfy it. Given 20 documents it could always find a passage that read like a match.
#
# The worst case: requirement 5.2/6 ("the AI policy is communicated within the
# organization") was scored met by quoting document 31 — "The IMS Policy is reviewed
# annually, communicated to all personnel..." That sentence is about the IMS Policy,
# not the AI policy. It passed on wording and failed on identity, and nothing was
# testing identity.
#
# So every requirement now carries four things the model cannot decide for itself:
#
#   subject      WHAT the passage must be about. A statement about a different
#                artefact is inadmissible however well it reads.
#   met_when     the acceptance test. What the passage has to actually say.
#   partial_when the only route to "partial". If the passage does not fit this
#                description, the verdict is met or unmet — never a hedge.
#   unmet_when   the near-misses that must NOT be credited, named explicitly,
#                because these are the ones the model reaches for.
#
# `actor` and `form` were already present and are kept: who must do it, and what kind
# of artefact satisfies it (determination / process / documented_information / record).

# ============================================================================
# UNIT 1 — CLAUSE 4.1. Clause only.
# The standard gives 4.1 no Annex A control and no Annex B guidance: its text
# contains no pointer to either (its NOTES cite ISO/IEC 22989, ISO/IEC 29100 and the
# NIST AI RMF, which are external references, not annexes of this standard). So every
# shortfall here is a potential nonconformity with no OFI layer to soften it.
# ============================================================================

CLAUSE_4_1 = {
    "unit": "context_of_the_organization",
    "title": "Understanding the organization and its context",
    "clause": "4.1",
    "controls": [],
    "guidance": [],
    "documented_information_required": False,  # says "determine" / "consider" only
    "requirements": [
        {
            "id": "4.1/0",
            "text": "External and internal issues relevant to the organization's purpose, that "
                    "affect its ability to achieve the intended result(s) of the AIMS, are determined",
            "subject": "this organization's own external and internal context",
            "actor": "organization",
            "form": "determination",
            "met_when": "specific external AND internal issues are named, and tied to this "
                        "organisation's ability to achieve its AIMS results — e.g. applicable AI "
                        "law, regulator expectations, its own governance, contractual obligations",
            "partial_when": "one side is present and the other absent (external issues named but "
                            "no internal, or the reverse), or issues are named without any link "
                            "to the AIMS",
            "unmet_when": "the document promises that context will be considered; or lists "
                          "generic industry or AI trends not tied to this organisation; or "
                          "states a scope or applicability instead of an issue",
            "look_for": [
                "external: applicable legal requirements, including prohibited uses of AI",
                "external: policies, guidelines and decisions from regulators",
                "external: incentives or consequences of the intended purpose and use of AI",
                "external: culture, traditions, values, norms and ethics around AI",
                "external: competitive landscape and trends for AI products and services",
                "internal: organizational context, governance, objectives, policies, procedures",
                "internal: contractual obligations",
                "internal: intended purpose of the AI system to be developed or used",
            ],
        },
        {
            "id": "4.1/1",
            "text": "Whether climate change is a relevant issue has been determined",
            "subject": "climate change, as an issue for this organization",
            "actor": "organization",
            "form": "determination",
            "met_when": "an explicit determination is stated — climate change IS a relevant issue "
                        "(and what follows from that), or is NOT relevant (and why)",
            "partial_when": "climate change is named as a topic but no determination of relevance "
                            "is reached",
            "unmet_when": "the document is silent on climate change. Sustainability, ESG, "
                          "environmental responsibility and societal-impact statements are NOT "
                          "determinations about climate change — this substitution was made in "
                          "testing and must be refused",
            "look_for": ["an explicit statement that climate change is, or is not, relevant here"],
        },
        {
            "id": "4.1/2",
            "text": "The intended purpose of the AI system(s) that are developed, provided or used "
                    "by the organization is considered",
            "subject": "the organization's own AI system(s)",
            "actor": "organization",
            "form": "determination",
            "met_when": "the purpose of the organisation's AI system(s) is stated — what each "
                        "system is FOR — identifiably about its actual systems",
            "partial_when": "systems are named or described without stating what they are for, or "
                            "purpose is given for some systems and not others",
            "unmet_when": "AI is discussed in general terms, or principles for AI use are stated, "
                          "without saying what any of this organisation's systems is for",
            "look_for": ["what each AI system is for",
                         "whether each system is developed, provided, or used by the organization"],
        },
        {
            "id": "4.1/3",
            # The enumeration is IN the text: it is what "role" MEANS here. Testing showed
            # the model otherwise reads "role" as an internal job title.
            "text": "The organization's role(s) with respect to those AI systems are determined — "
                    "that is, whether it acts as an AI provider, AI producer, AI customer, "
                    "AI partner, AI subject, or relevant authority",
            "subject": "the organization's role in the ISO/IEC 42001 sense (provider, producer, "
                       "customer, partner, subject, authority) — NOT its internal job titles",
            "actor": "organization",
            "form": "determination",
            "met_when": "the organisation's role(s) are identified in these terms, or stated "
                        "equivalently and unmistakably (e.g. 'we develop and deploy our own AI "
                        "systems and also procure third-party AI tools', which identifies producer "
                        "and customer)",
            "partial_when": "the document says it develops or uses AI systems, but never connects "
                            "that to a determination of its role",
            "unmet_when": "the only role content is internal responsibilities — a table of CEO, "
                          "CAIO, CTO duties. That is clause 5.3 evidence, not 4.1. This "
                          "substitution was made in testing and must be refused",
            "look_for": [
                "AI provider: AI platform providers, AI product or service providers",
                "AI producer: developers, designers, operators, testers and evaluators, deployers, "
                "human factor professionals, domain experts, impact assessors, procurers, "
                "governance and oversight professionals",
                "AI customer: including AI users",
                "AI partner: AI system integrators, data providers",
                "AI subject: data subjects and other subjects",
                "relevant authorities: policymakers and regulators",
                "the role may follow from data categories processed (PII controller or PII "
                "processor), or from legal requirements specific to AI systems",
            ],
            "note": "The organization's roles can determine the applicability and extent of "
                    "applicability of the requirements and controls in this document.",
        },
    ],
}


# ============================================================================
# UNIT 2 — AI POLICY. Clause 5.2 + controls A.2.2/A.2.3/A.2.4 + guidance B.2.
# Grouped because clause 5.2 says so: "Control objectives and controls for
# establishing an AI policy are provided in A.2 in Table A.1. Implementation
# guidance for these controls is provided in B.2."
#
# All eight clause requirements share ONE subject: the AI policy. That single fact
# is what makes the IMS Policy quote inadmissible on 5.2/6 and 5.2/7.
# ============================================================================

AI_POLICY = {
    "unit": "ai_policy",
    "title": "AI policy",
    "clause": "5.2",
    "control_codes": ["A.2.2", "A.2.3", "A.2.4"],
    "guidance_sections": ["B.2.2", "B.2.3", "B.2.4"],
    "requirements": [
        # ---- Layer 1: clause 5.2 (mandatory, not excludable) -----------------
        {
            "id": "5.2/0",
            "text": "An AI policy is established that is appropriate to the purpose of the organization",
            "subject": "the AI policy",
            "actor": "top_management",
            "form": "documented_information",
            "met_when": "the AI policy connects itself to this organisation's purpose, mission, "
                        "business or the nature of its AI activities",
            "partial_when": "the policy states a purpose for itself but does not connect it to the "
                            "organisation's purpose (e.g. 'innovation and competitive advantage' "
                            "with no tie to what this organisation is for)",
            "unmet_when": "no AI policy exists, or it is generic text that would fit any company",
        },
        {
            "id": "5.2/1",
            "text": "The AI policy provides a framework for setting AI objectives (see 6.2)",
            "subject": "the AI policy, and the setting of AI objectives",
            "actor": "top_management",
            "form": "documented_information",
            "met_when": "the policy states that AI objectives are established within it, in "
                        "accordance with it, or by a process it defines",
            "partial_when": "the policy mentions AI objectives but does not present itself as the "
                            "framework for setting them",
            "unmet_when": "the policy is silent on AI objectives. Objectives existing in a "
                          "SEPARATE document does NOT satisfy this — the requirement is that the "
                          "POLICY provides the framework. Statements of ambition, principles or "
                          "opportunity are not an objectives framework; this substitution was "
                          "made in testing and must be refused",
        },
        {
            "id": "5.2/2",
            "text": "The AI policy includes a commitment to meet applicable requirements",
            "subject": "the AI policy",
            "actor": "top_management",
            "form": "documented_information",
            "met_when": "the policy commits to complying with applicable requirements — legal, "
                        "regulatory, contractual, or other obligations the organisation subscribes to",
            "partial_when": "it commits to some categories only (laws and regulations but not "
                            "contractual or other subscribed obligations)",
            "unmet_when": "no commitment to comply appears; compliance is only described as "
                          "someone's job in a responsibilities table",
        },
        {
            "id": "5.2/3",
            "text": "The AI policy includes a commitment to continual improvement of the AI "
                    "management system",
            "subject": "the AI policy, and the AIMS specifically",
            "actor": "top_management",
            "form": "documented_information",
            "met_when": "the policy commits to continually improving the AI MANAGEMENT SYSTEM",
            "partial_when": "improvement is expressed aspirationally or culturally ('a culture of "
                            "continuous improvement') without committing to improving the AIMS",
            "unmet_when": "no improvement commitment of any kind; or improvement of AI systems' "
                          "performance only, which is a different thing from improving the AIMS",
        },
        {
            "id": "5.2/4",
            "text": "The AI policy is available as documented information",
            "subject": "the AI policy as a document",
            "actor": "organization",
            "form": "documented_information",
            "met_when": "the AI policy exists as a controlled document — identifiable, versioned, "
                        "approved, retrievable",
            "partial_when": "it exists but lacks control attributes (no version, no approval, no "
                            "identifier)",
            "unmet_when": "the policy is described or referred to but its text is not present",
        },
        {
            "id": "5.2/5",
            "text": "The AI policy refers, as relevant, to other organizational policies",
            "subject": "the AI policy, and the other policies it interfaces with",
            "actor": "organization",
            "form": "documented_information",
            "met_when": "the AI policy names other organisational policies it relates to and "
                        "indicates the relationship (quality, information security, privacy, "
                        "risk management, procurement, HR conduct)",
            "partial_when": "one or two other policies are mentioned in passing, with no statement "
                            "of how they interface",
            "unmet_when": "no other organisational policy is named. Another document referring to "
                          "the AI policy is the reverse direction and does not satisfy this",
        },
        {
            "id": "5.2/6",
            "text": "The AI policy is communicated within the organization",
            "subject": "the AI policy — NOT any other policy",
            "actor": "organization",
            "form": "record",
            "met_when": "a passage states how THIS AI POLICY is communicated internally "
                        "(publication, induction, mandatory training, attestation), or evidences "
                        "that it was",
            "partial_when": "an intention to communicate is stated with no mechanism, or only "
                            "future amendments are said to be communicated",
            "unmet_when": "nothing addresses communication of the AI policy. A statement about a "
                          "DIFFERENT policy being communicated — the IMS Policy, the Quality "
                          "Policy — is inadmissible: this exact substitution was made in testing "
                          "and scored met, and it must be refused",
        },
        {
            "id": "5.2/7",
            "text": "The AI policy is available to interested parties, as appropriate",
            "subject": "the AI policy — NOT any other policy",
            "actor": "organization",
            "form": "record",
            "met_when": "a passage states that this AI policy is available outside the "
                        "organisation, or gives the route by which an interested party obtains it",
            "partial_when": "availability is asserted ('on request') with no route, owner or "
                            "process",
            "unmet_when": "nothing addresses external availability; or a statement about a "
                          "different policy is offered",
            "contradiction_watch": "the AI policy's own classification or confidentiality notice. "
                                   "'Internal — Controlled Document', 'internal use only', "
                                   "'unauthorized reproduction prohibited' CONTRADICT this "
                                   "requirement. Where both appear, the verdict is 'contradicted' "
                                   "and both passages must be quoted. In testing the contradicting "
                                   "notice was present in the prompt and was missed.",
        },
        # ---- Layer 2: Annex A controls (excludable via the SoA) --------------
        {
            "id": "A.2.2/0",
            "text": "A policy for the development or use of AI systems is documented",
            "subject": "a documented policy covering AI development or use",
            "actor": "organization",
            "form": "documented_information",
            "met_when": "a policy document exists whose stated scope covers the development "
                        "and/or use of AI systems",
            "partial_when": "AI is covered only as a sub-section of a broader policy without "
                            "stated scope over AI development or use",
            "unmet_when": "no policy covers AI development or use",
        },
        {
            "id": "A.2.3/0",
            "text": "Other policies that can be affected by, or apply to, the organization's "
                    "objectives with respect to AI systems are determined",
            "subject": "the organization's other policies, in relation to its AI objectives",
            "actor": "organization",
            "form": "determination",
            "met_when": "the organisation identifies WHICH other policies intersect with its AI "
                        "objectives — named, as a determination",
            "partial_when": "other policies are named but not in relation to AI objectives",
            "unmet_when": "no determination is made. A job description saying someone 'ensures "
                          "alignment' is a responsibility, not a determination; this substitution "
                          "was made in testing and must be refused",
        },
        {
            "id": "A.2.3/1",
            "text": "The relationship between the AI policy and those other policies is addressed",
            "subject": "the relationship between the AI policy and other policies",
            "actor": "organization",
            "form": "documented_information",
            "met_when": "the relationship is set out — which prevails, how conflicts resolve, or "
                        "which provisions were added to which policy",
            "partial_when": "cross-references exist without any statement of the relationship",
            "unmet_when": "no relationship is addressed anywhere",
        },
        {
            "id": "A.2.4/0",
            "text": "The AI policy is reviewed at planned intervals, and additionally as needed",
            "subject": "review of the AI policy",
            "actor": "organization",
            "form": "process",
            "met_when": "a stated interval for reviewing the AI policy exists, plus triggers for "
                        "out-of-cycle review",
            "partial_when": "an interval is stated with no additional triggers, or triggers with "
                            "no interval",
            "unmet_when": "no review arrangement for the AI policy is stated",
        },
        {
            "id": "A.2.4/1",
            "text": "The review addresses the policy's continuing suitability, adequacy and "
                    "effectiveness",
            "subject": "the content and outcome of the AI policy review",
            "actor": "organization",
            "form": "record",
            "met_when": "a review has been performed, or its defined scope covers suitability, "
                        "adequacy AND effectiveness",
            "partial_when": "the review is defined but covers only some of the three, or is "
                            "planned and not yet evidenced as performed",
            "unmet_when": "no review content is stated. Note the form is 'record': a procedure "
                          "saying reviews happen annually is not evidence that one happened",
        },
    ],
}
