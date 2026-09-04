# ISO/IEC 42001 — Judgement Rules

The acceptance test for every requirement in clauses 4–10, with each clause's
Annex A / Annex B mapping. **This is a review document.** The tests are judgement
calls about where a bar sits; nothing should be built on them until they are checked.

## How to read a requirement

| Field | What it does |
|---|---|
| **subject** | what a passage must be *about*. A statement about a different artefact is inadmissible however well the wording fits — this is the test that stops a sentence about the *IMS Policy* satisfying an *AI policy* requirement. |
| **actor** | `organization` or `top_management`, exactly as the clause names it. Where it is top management, evidence must show an act — an approval, a signature, a minuted decision — not a document's claim that they are committed. |
| **form** | what kind of artefact satisfies it. A procedure saying reviews happen annually is not evidence that a review happened. |
| **met_when** | what a passage must actually say. |
| **partial_when** | the *only* route to a partial verdict. If evidence does not fit this description, the verdict is met or unmet — never a hedge for uncertainty. |
| **unmet_when** | near-misses that must not be credited, named so they can be refused. |
| **look for** | informative search aids from the clause's NOTES. NOTEs are informative in ISO, so these carry no verdict and can never make a requirement unmet. |

Forms: **determination** — the organisation has worked the thing out and can show it · **process** — a defined, repeatable way of doing it exists · **documented_information** — it exists as a document, available for use · **record** — evidence that it actually happened, at least once

## Totals

```
clauses 4-10        32 subclauses
requirements        174 across those clauses
Annex A             38 controls
Annex B             248 guidance points
```

## Clause → Annex A / Annex B

Taken from pointers written in the standard's own text. **24 of 32 clauses have no
annex link at all** — including every clause in 4, 9 and 10. Only 5 point at specific
controls. The remaining 22 controls are reachable only through 6.1.3, from the risk
assessment: controls attach to **risks**, not to clauses.

| Clause | Title | Annex A controls | Annex B points |
|---|---|---|---|
| 4.1 | Understanding the organization and its context | — | — |
| 4.2 | Understanding the needs and expectations of interested parties | — | — |
| 4.3 | Determining the scope of the AI management system | — | — |
| 4.4 | AI management system | — | — |
| 5.1 | Leadership and commitment | — | — |
| **5.2** | AI policy | A.2.2, A.2.3, A.2.4 | 17 |
| **5.3** | Roles, responsibilities and authorities | A.3.2 | 13 |
| 6.1.1 | Actions to address risks and opportunities - General | — | — |
| 6.1.2 | AI risk assessment | — | — |
| **6.1.3** | AI risk treatment | *all of Annex A — selection / implementation rule* | — |
| **6.1.4** | AI system impact assessment | A.5.2, A.5.3, A.5.4, A.5.5 | 29 |
| **6.2** | AI objectives and planning to achieve them | A.6.1.2, A.6.1.3, A.9.3 | 29 |
| 6.3 | Planning of changes | — | — |
| **7.1** | Resources | A.4.2, A.4.3, A.4.4, A.4.5, A.4.6 | 30 |
| **7.2** | Competence | *none — guidance B.4.6 only* | — |
| 7.3 | Awareness | — | — |
| 7.4 | Communication | — | — |
| 7.5.1 | Documented information - General | — | — |
| 7.5.2 | Creating and updating documented information | — | — |
| 7.5.3 | Control of documented information | — | — |
| **8.1** | Operational planning and control | *all of Annex A — selection / implementation rule* | — |
| 8.2 | AI risk assessment (operation) | — | — |
| 8.3 | AI risk treatment (operation) | — | — |
| 8.4 | AI system impact assessment (operation) | — | — |
| 9.1 | Monitoring, measurement, analysis and evaluation | — | — |
| 9.2.1 | Internal audit - General | — | — |
| 9.2.2 | Internal audit programme | — | — |
| 9.3.1 | Management review - General | — | — |
| 9.3.2 | Management review inputs | — | — |
| 9.3.3 | Management review results | — | — |
| 10.1 | Continual improvement | — | — |
| 10.2 | Nonconformity and corrective action | — | — |

Controls reachable from a clause pointer: **16 of 38**. The other **22** — A.7 data, A.8 information for interested parties, A.10 third-party relationships, most of A.6.2 life cycle — are reachable only via 6.1.3.

### The pointers, quoted

**5.2** — *"Control objectives and controls for establishing an AI policy are provided in A.2 in Table A.1. Implementation guidance for these controls is provided in B.2."*

**5.3** — *"NOTE A control for defining and allocating roles and responsibilities is provided in A.3.2 in Table A.1. Implementation guidance for this control is provided in B.3.2."*

**6.1.3** — *"determine all controls that are necessary ... and compare the controls with those in Annex A to verify that no necessary controls have been omitted ... consider the guidance in Annex B"*

**6.1.4** — *"A.5 in Table A.1 provides controls for assessing impacts of AI systems."*

**6.2** — *"Control objectives and controls for identifying objectives for responsible development and use of AI systems and measures to achieve them are provided in A.6.1 and A.9.3 in Table A.1. Implementation guidance for these controls is provided in B.6.1 and B.9.3."*

**7.1** — *"NOTE Control objectives and controls for AI resources are provided in A.4 in Table A.1. Implementation guidance for these controls is provided in Clause B.4."*

**7.2** — *"NOTE 1 Implementation guidance for human resources including consideration of necessary expertise is provided in B.4.6."*

**8.1** — *"The organization shall implement the controls determined according to 6.1.3 ... Annex A lists reference controls and Annex B provides implementation guidance for them."*

## Assessment units

The mapping above gives the grouping. A unit is assessed in one call; its layers are
graded separately, because the consequence of failing each differs:

```
clause requirement unmet    -> nonconformity. Clauses cannot be excluded.
control requirement unmet   -> nonconformity ONLY if the control is applicable
                               per the Statement of Applicability.
Annex B point unaddressed   -> opportunity for improvement. NEVER a nonconformity,
                               because every verb in Annex B is 'should'.
```

- **5 merged units** — clause + its controls + their Annex B: 5.2, 5.3, 6.1.4, 6.2, 7.1
- **27 clause-only units** — no annex layer, so every shortfall is a potential nonconformity with no OFI layer to soften it
- **22 control-only units** — controls with no clause pointer, plus their Annex B

---

# The rules, clause by clause

## 4.1 — Understanding the organization and its context

*4 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `4.1/0` The organization shall determine external and internal issues that are relevant to its purpose and that affect its ability to achieve the intended result(s) of its AI management system.

- **subject** — external and internal issues relevant to the organization's purpose and affecting the AI management system's intended results
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies specific external and internal issues (such as legal requirements, culture, governance, objectives, etc.) and explains their relevance to the organization's purpose and their impact on achieving the intended results of the AI management system
- **partial when** — only external OR only internal issues are determined, or issues are listed without explaining their relevance or impact
- **unmet when** — issues are not determined, or only general statements about context are made without identifying specific issues or their relevance
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - external context considerations: legal requirements, prohibited uses, regulator policies, incentives, culture, competitive landscape
  - internal context considerations: governance, objectives, policies, procedures, contractual obligations, intended purpose of AI system

### `4.1/1` The organization shall determine whether climate change is a relevant issue.

- **subject** — climate change as a relevant issue for the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage explicitly states whether climate change is considered a relevant issue for the AI management system, with reasoning or evidence of consideration
- **partial when** — climate change is mentioned as a possible issue but no determination is made
- **unmet when** — climate change is not addressed, or only general environmental issues are discussed without specific reference to climate change

### `4.1/2` The organization shall consider the intended purpose of the AI system(s) that are developed, provided or used by the organization.

- **subject** — intended purpose of the AI system(s) developed, provided or used
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage describes the intended purpose(s) of the AI system(s) the organization develops, provides, or uses, showing consideration in the context of the AI management system
- **partial when** — intended purpose is referenced but not described or only some AI systems are considered
- **unmet when** — intended purpose is not considered, or only general statements about AI systems are made without reference to their purpose
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - intended purpose of AI system to be developed or used

### `4.1/3` The organization shall determine its roles with respect to these AI systems.

- **subject** — the organization's roles with respect to the AI systems it develops, provides or uses
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies the organization's specific roles (such as AI provider, producer, customer, partner, subject, authority) with respect to its AI systems, referencing relevant frameworks or standards if applicable
- **partial when** — roles are mentioned but not determined, or only some roles are identified without clarity
- **unmet when** — roles are not determined, or only responsibilities are described without reference to roles
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - roles: AI provider, producer, customer, partner, subject, authority
  - roles informed by legal requirements or data categories (e.g. PII processor/controller)


## 4.2 — Understanding the needs and expectations of interested parties

*3 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `4.2/0` The organization shall determine the interested parties that are relevant to the AI management system

- **subject** — interested parties relevant to the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies specific groups, individuals, or entities considered relevant to the AI management system (e.g., customers, regulators, suppliers, employees, society)
- **partial when** — a passage lists some but not all relevant interested parties, or states an intention to identify them without evidence of completion
- **unmet when** — a passage discusses interested parties in general without linking them to the AI management system, or references a determination without showing its content
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Relevant interested parties can have requirements related to climate change.

### `4.2/1` The organization shall determine the relevant requirements of these interested parties

- **subject** — requirements of the relevant interested parties
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies specific requirements, needs, or expectations of the relevant interested parties (e.g., legal, ethical, performance, climate change concerns) in relation to the AI management system
- **partial when** — a passage identifies requirements for some but not all relevant interested parties, or states an intention to determine requirements without evidence of completion
- **unmet when** — a passage discusses requirements in general without linking them to the relevant interested parties, or references a determination without showing its content
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Relevant interested parties can have requirements related to climate change.

### `4.2/2` The organization shall determine which of these requirements will be addressed through the AI management system

- **subject** — requirements of relevant interested parties to be addressed by the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage specifies which requirements of relevant interested parties the AI management system will address, with clear inclusion or exclusion criteria
- **partial when** — a passage indicates some requirements will be addressed but does not specify which, or states an intention to address requirements without evidence of completion
- **unmet when** — a passage discusses requirements without linking them to the AI management system, or references a determination without showing its content
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Relevant interested parties can have requirements related to climate change.


## 4.3 — Determining the scope of the AI management system

*5 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `4.3/0` The organization shall determine the boundaries and applicability of the AI management system to establish its scope.

- **subject** — boundaries and applicability of the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage describes how the organization has worked out what parts of its operations, functions, or sites are included or excluded from the AI management system, and what the system applies to
- **partial when** — a passage describes only boundaries or only applicability, or states an intention to determine scope without evidence it has been done
- **unmet when** — a passage describes the scope of a different management system, or only assigns responsibility for determining scope, or references an unseen document

### `4.3/1` When determining this scope, the organization shall consider the external and internal issues referred to in 4.1.

- **subject** — external and internal issues referred to in 4.1
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows that the organization has taken into account both external and internal issues (as defined in 4.1) when establishing the scope of the AI management system
- **partial when** — a passage shows consideration of only external or only internal issues, or states an intention to consider issues without evidence it has been done
- **unmet when** — a passage describes issues unrelated to 4.1, or only references 4.1 without showing consideration, or describes issues for a different management system
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Examples of external and internal issues include legal, regulatory, technological, organizational, and market factors.

### `4.3/2` When determining this scope, the organization shall consider the requirements referred to in 4.2.

- **subject** — requirements referred to in 4.2
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows that the organization has taken into account the requirements of interested parties (as defined in 4.2) when establishing the scope of the AI management system
- **partial when** — a passage shows consideration of only some requirements of interested parties, or states an intention to consider requirements without evidence it has been done
- **unmet when** — a passage describes requirements unrelated to 4.2, or only references 4.2 without showing consideration, or describes requirements for a different management system
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Requirements of interested parties may include legal, regulatory, contractual, and stakeholder expectations.

### `4.3/3` The scope shall be available as documented information.

- **subject** — scope of the AI management system
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage confirms the existence of a document (or equivalent artefact) that states the scope of the AI management system
- **partial when** — a passage describes a draft or incomplete scope document, or states an intention to document the scope
- **unmet when** — a passage describes the scope verbally or references an unseen document, or documents the scope of a different management system

### `4.3/4` The scope of the AI management system shall determine the organization’s activities with respect to this document’s requirements on the AI management system, leadership, planning, support, operation, performance, evaluation, improvement, controls and objectives.

- **subject** — organization’s activities with respect to the requirements of ISO/IEC 42001:2023
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows that the scope of the AI management system defines which organizational activities are subject to the requirements of ISO/IEC 42001:2023, including leadership, planning, support, operation, performance, evaluation, improvement, controls, and objectives
- **partial when** — a passage shows the scope determines only some activities, or states an intention to use the scope for this purpose without evidence it has been done
- **unmet when** — a passage describes activities unrelated to the AI management system or to ISO/IEC 42001:2023, or references an unseen artefact


## 4.4 — AI management system

*5 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `4.4/0` The organization shall establish an AI management system, including the processes needed and their interactions, in accordance with the requirements of this document.

- **subject** — the AI management system and its processes and interactions
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage describes that an AI management system has been established, specifying the processes needed and their interactions, and states alignment with ISO/IEC 42001 requirements
- **partial when** — a passage describes establishment of an AI management system but omits processes, interactions, or reference to ISO/IEC 42001 requirements
- **unmet when** — a passage describes establishment of a management system for a different topic (e.g., quality, information security), or only assigns responsibility without evidence of establishment

### `4.4/1` The organization shall implement an AI management system, including the processes needed and their interactions, in accordance with the requirements of this document.

- **subject** — the implementation of the AI management system and its processes and interactions
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how the AI management system and its processes and interactions are put into practice, referencing ISO/IEC 42001 requirements
- **partial when** — a passage describes implementation of some but not all processes or interactions, or lacks reference to ISO/IEC 42001 requirements
- **unmet when** — a passage describes implementation of a management system for a different topic, or only describes planning without actual implementation

### `4.4/2` The organization shall maintain an AI management system, including the processes needed and their interactions, in accordance with the requirements of this document.

- **subject** — the maintenance of the AI management system and its processes and interactions
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes ongoing activities to keep the AI management system and its processes and interactions operational and effective, referencing ISO/IEC 42001 requirements
- **partial when** — a passage describes maintenance of some but not all processes or interactions, or lacks reference to ISO/IEC 42001 requirements
- **unmet when** — a passage describes maintenance of a management system for a different topic, or only describes maintenance plans without evidence of ongoing activity

### `4.4/3` The organization shall continually improve an AI management system, including the processes needed and their interactions, in accordance with the requirements of this document.

- **subject** — the continual improvement of the AI management system and its processes and interactions
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a defined process for continual improvement of the AI management system and its processes and interactions, referencing ISO/IEC 42001 requirements
- **partial when** — a passage describes improvement activities for some but not all processes or interactions, or lacks reference to ISO/IEC 42001 requirements
- **unmet when** — a passage describes improvement of a management system for a different topic, or only describes intentions without a defined process

### `4.4/4` The organization shall document an AI management system, including the processes needed and their interactions, in accordance with the requirements of this document.

- **subject** — the documentation of the AI management system and its processes and interactions
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage evidences the existence of documented information describing the AI management system, its processes, their interactions, and alignment with ISO/IEC 42001 requirements
- **partial when** — a passage evidences documentation of some but not all processes or interactions, or lacks reference to ISO/IEC 42001 requirements
- **unmet when** — a passage evidences documentation of a management system for a different topic, or only references undocumented practices


## 5.1 — Leadership and commitment

*8 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `5.1/0` Top management shall ensure that the AI policy and AI objectives are established and are compatible with the strategic direction of the organization

- **subject** — establishment and compatibility of AI policy and AI objectives with strategic direction
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage shows that top management has established the AI policy and AI objectives, and confirms their compatibility with the organization's strategic direction (e.g., explicit statements, board minutes, signed policy documents referencing strategic direction)
- **partial when** — only the establishment of AI policy or objectives is shown, but not their compatibility with strategic direction; or compatibility is asserted for only one (policy or objectives)
- **unmet when** — statements about establishing AI policy or objectives without reference to strategic direction; statements about strategic direction without mention of AI policy or objectives; references to other policies or objectives not related to AI
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - References to core activities or purposes of the organization as part of strategic direction

### `5.1/1` Top management shall ensure the integration of the AI management system requirements into the organization’s business processes

- **subject** — integration of AI management system requirements into business processes
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage demonstrates that AI management system requirements are incorporated into business processes (e.g., process maps, integration statements, workflow documentation showing AI requirements embedded)
- **partial when** — integration is shown for some but not all relevant business processes; or only an intention to integrate is stated
- **unmet when** — statements about business processes without mention of AI management system requirements; statements about AI management system requirements without reference to business processes; references to integration in unrelated systems
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Business interpreted broadly as core activities or purposes

### `5.1/2` Top management shall ensure that the resources needed for the AI management system are available

- **subject** — availability of resources for the AI management system
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage confirms that resources (personnel, financial, technical, etc.) required for the AI management system are made available (e.g., resource allocation statements, budget approvals, staffing plans)
- **partial when** — only some types of resources are addressed; or an intention to provide resources is stated without evidence of actual availability
- **unmet when** — statements about resources for other systems; statements about resource needs without confirmation of availability; references to AI management system without mention of resources

### `5.1/3` Top management shall communicate the importance of effective AI management and of conforming to the AI management system requirements

- **subject** — communication of importance of effective AI management and conformity to AI management system requirements
- **actor** — `top_management` · **form** — `record`
- **met when** — a passage evidences that top management has communicated (e.g., emails, presentations, meeting minutes, internal memos) the importance of effective AI management and the need to conform to AI management system requirements
- **partial when** — communication covers only one aspect (either effective AI management or conformity to requirements); or an intention to communicate is stated without evidence of actual communication
- **unmet when** — statements about communication of unrelated topics; statements about AI management or requirements without evidence of communication; references to communication plans without evidence of execution
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Culture of responsible approach to AI use, development, and governance

### `5.1/4` Top management shall ensure that the AI management system achieves its intended result(s)

- **subject** — achievement of intended results of the AI management system
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage demonstrates that top management has determined whether the AI management system achieves its intended results (e.g., performance reviews, outcome assessments, management review minutes)
- **partial when** — only partial achievement is evidenced; or only an intention to monitor achievement is stated
- **unmet when** — statements about intended results without evidence of achievement; statements about achievement in unrelated systems; references to AI management system without mention of results

### `5.1/5` Top management shall direct and support persons to contribute to the effectiveness of the AI management system

- **subject** — direction and support for persons to contribute to AI management system effectiveness
- **actor** — `top_management` · **form** — `record`
- **met when** — a passage evidences that top management has directed and supported persons (e.g., staff, teams) to contribute to the effectiveness of the AI management system (e.g., directives, support statements, training records, resource provision)
- **partial when** — only direction or only support is evidenced; or only some persons are addressed
- **unmet when** — statements about direction or support in unrelated systems; statements about AI management system effectiveness without evidence of direction or support; references to plans without evidence of action
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Modelling a culture of responsible approach to AI

### `5.1/6` Top management shall promote continual improvement

- **subject** — promotion of continual improvement
- **actor** — `top_management` · **form** — `record`
- **met when** — a passage evidences that top management has promoted continual improvement (e.g., improvement initiatives, communications, process reviews, encouragement statements)
- **partial when** — only an intention to promote continual improvement is stated; or only one improvement initiative is evidenced without ongoing promotion
- **unmet when** — statements about improvement in unrelated systems; statements about continual improvement without evidence of promotion; references to improvement plans without evidence of action

### `5.1/7` Top management shall support other relevant roles to demonstrate their leadership as it applies to their areas of responsibility

- **subject** — support for other relevant roles to demonstrate leadership in their areas of responsibility
- **actor** — `top_management` · **form** — `record`
- **met when** — a passage evidences that top management has supported other relevant roles (e.g., department heads, project leads) to demonstrate leadership in their areas of responsibility (e.g., empowerment statements, delegation records, leadership development programs)
- **partial when** — only some relevant roles are supported; or only an intention to support is stated
- **unmet when** — statements about support for unrelated roles; statements about leadership without evidence of support; references to support plans without evidence of action
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Ensuring awareness of and compliance with responsible approach to AI


## 5.2 — AI policy

*8 requirements · Annex A: A.2.2, A.2.3, A.2.4*

### `5.2/0` Top management shall establish an AI policy that is appropriate to the purpose of the organization

- **subject** — the AI policy's appropriateness to the organization's purpose
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage demonstrates that the AI policy aligns with, supports, or is tailored to the organization's stated purpose, mission, or business context
- **partial when** — the AI policy is stated but only partially addresses the organization's purpose, or the purpose is referenced but not clearly linked to the policy
- **unmet when** — the AI policy is generic with no reference to the organization's purpose, or only the organization's purpose is described without linking to the AI policy
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Considerations for organizations when developing AI policies are provided in ISO/IEC 38507.

### `5.2/1` Top management shall establish an AI policy that provides a framework for setting AI objectives (see 6.2)

- **subject** — the AI policy's framework for setting AI objectives
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage shows the AI policy includes principles, criteria, or structure for setting AI objectives, referencing how objectives are derived or guided
- **partial when** — the AI policy mentions objectives but lacks a clear framework or only provides partial guidance
- **unmet when** — the AI policy omits any mention of objectives or framework, or only lists objectives without a guiding framework
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Considerations for organizations when developing AI policies are provided in ISO/IEC 38507.

### `5.2/2` Top management shall establish an AI policy that includes a commitment to meet applicable requirements

- **subject** — the AI policy's commitment to meet applicable requirements
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage in the AI policy explicitly states a commitment to comply with legal, regulatory, contractual, or other applicable requirements relevant to AI
- **partial when** — the AI policy references requirements but lacks a clear commitment, or only commits to some requirements
- **unmet when** — the AI policy omits any mention of applicable requirements, or only describes requirements without a commitment
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Considerations for organizations when developing AI policies are provided in ISO/IEC 38507.

### `5.2/3` Top management shall establish an AI policy that includes a commitment to continual improvement of the AI management system

- **subject** — the AI policy's commitment to continual improvement of the AI management system
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage in the AI policy explicitly states a commitment to continual improvement of the AI management system
- **partial when** — the AI policy references improvement but lacks a clear commitment, or only commits to improvement in some areas
- **unmet when** — the AI policy omits any mention of continual improvement, or only describes improvement activities without a commitment
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Considerations for organizations when developing AI policies are provided in ISO/IEC 38507.

### `5.2/4` The AI policy shall be available as documented information

- **subject** — the AI policy as a document
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage evidences the existence of a documented AI policy (e.g., a file, manual, or official document)
- **partial when** — a draft or incomplete version of the AI policy is available, or only a summary is documented
- **unmet when** — no documented AI policy exists, or only references to an undocumented policy are provided
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Considerations for organizations when developing AI policies are provided in ISO/IEC 38507.

### `5.2/5` The AI policy shall refer as relevant to other organizational policies

- **subject** — the AI policy's references to other organizational policies
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage in the AI policy refers to other relevant organizational policies (e.g., information security, quality, ethics), showing linkage or alignment
- **partial when** — the AI policy references some but not all relevant policies, or only mentions policies without clear relevance
- **unmet when** — the AI policy omits any reference to other organizational policies, or references policies unrelated to AI
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Considerations for organizations when developing AI policies are provided in ISO/IEC 38507.

### `5.2/6` The AI policy shall be communicated within the organization

- **subject** — the AI policy - NOT any other policy
- **actor** — `organization` · **form** — `record`
- **met when** — a passage states how THIS AI POLICY is communicated internally (publication, induction, mandatory training, attestation), or evidences that it was
- **partial when** — an intention to communicate is stated with no mechanism, or only future amendments are said to be communicated
- **unmet when** — nothing addresses communication of the AI policy. A statement about a DIFFERENT policy being communicated - the IMS Policy, the Quality Policy - is inadmissible
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Considerations for organizations when developing AI policies are provided in ISO/IEC 38507.

### `5.2/7` The AI policy shall be available to interested parties, as appropriate

- **subject** — the AI policy's availability to interested parties
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the AI policy is made available to relevant interested parties (e.g., customers, regulators, partners), with description of how and to whom
- **partial when** — the AI policy is available to some but not all appropriate interested parties, or only an intention to make it available is stated
- **unmet when** — no evidence the AI policy is available to interested parties, or only internal availability is described
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Considerations for organizations when developing AI policies are provided in ISO/IEC 38507.


## 5.3 — Roles, responsibilities and authorities

*4 requirements · Annex A: A.3.2*

### `5.3/0` Responsibilities and authorities for relevant roles are assigned within the organization

- **subject** — assignment of responsibilities and authorities for relevant roles
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage identifies specific roles and states that responsibilities and authorities have been assigned to those roles
- **partial when** — roles are listed but responsibilities and authorities are only partially assigned, or only some relevant roles are covered
- **unmet when** — no assignment of responsibilities and authorities is described, or only a general statement about roles without specifying assignment
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - A control for defining and allocating roles and responsibilities is provided in A.3.2 in Table A.1. Implementation guidance for this control is provided in B.3.2.

### `5.3/1` Responsibilities and authorities for relevant roles are communicated within the organization

- **subject** — communication of assigned responsibilities and authorities for relevant roles
- **actor** — `top_management` · **form** — `record`
- **met when** — a passage evidences that assigned responsibilities and authorities for relevant roles have been communicated (e.g., via internal memos, training, publication, or attestation)
- **partial when** — an intention to communicate is stated but no evidence of actual communication, or only some roles' responsibilities and authorities are communicated
- **unmet when** — no evidence of communication, or communication about unrelated topics (e.g., general organizational structure)
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - A control for defining and allocating roles and responsibilities is provided in A.3.2 in Table A.1. Implementation guidance for this control is provided in B.3.2.

### `5.3/2` Responsibility and authority are assigned for ensuring that the AI management system conforms to the requirements of this document

- **subject** — assignment of responsibility and authority for AI management system conformity
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage identifies a specific role or person assigned responsibility and authority for ensuring conformity to ISO/IEC 42001:2023
- **partial when** — responsibility or authority is assigned but not both, or assignment is implied but not explicit
- **unmet when** — no assignment is made, or assignment is for a different standard or system
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - A control for defining and allocating roles and responsibilities is provided in A.3.2 in Table A.1. Implementation guidance for this control is provided in B.3.2.

### `5.3/3` Responsibility and authority are assigned for reporting on the performance of the AI management system to top management

- **subject** — assignment of responsibility and authority for reporting AI management system performance
- **actor** — `top_management` · **form** — `determination`
- **met when** — a passage identifies a specific role or person assigned responsibility and authority for reporting on AI management system performance to top management
- **partial when** — responsibility or authority is assigned but not both, or assignment is implied but not explicit
- **unmet when** — no assignment is made, or assignment is for reporting on a different system or to a different audience
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - A control for defining and allocating roles and responsibilities is provided in A.3.2 in Table A.1. Implementation guidance for this control is provided in B.3.2.


## 6.1.1 — Actions to address risks and opportunities - General

*15 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `6.1.1/0` The organization shall consider the issues referred to in 4.1 and the requirements referred to in 4.2 when planning for the AI management system

- **subject** — issues from 4.1 and requirements from 4.2 in AI management system planning
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows the organization has reviewed and taken into account the issues from clause 4.1 and requirements from clause 4.2 during AI management system planning
- **partial when** — only issues from 4.1 OR requirements from 4.2 are considered, not both
- **unmet when** — no evidence that either 4.1 or 4.2 are considered; evidence refers to unrelated issues or requirements

### `6.1.1/1` The organization shall determine the risks and opportunities that need to be addressed to give assurance that the AI management system can achieve its intended result(s)

- **subject** — risks and opportunities related to achieving intended results of the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies specific risks and opportunities that, if addressed, will help assure the AI management system achieves its intended results
- **partial when** — risks or opportunities are identified but not linked to achieving intended results
- **unmet when** — risks and opportunities are not determined, or only general statements about assurance are made without specifics

### `6.1.1/2` The organization shall determine the risks and opportunities that need to be addressed to prevent or reduce undesired effects

- **subject** — risks and opportunities related to preventing or reducing undesired effects
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies risks and opportunities that, if addressed, will prevent or reduce undesired effects from the AI management system
- **partial when** — risks or opportunities are identified but not linked to undesired effects
- **unmet when** — no evidence of risks and opportunities determined for undesired effects; only general statements about prevention or reduction

### `6.1.1/3` The organization shall determine the risks and opportunities that need to be addressed to achieve continual improvement

- **subject** — risks and opportunities related to continual improvement
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies risks and opportunities that, if addressed, will support continual improvement of the AI management system
- **partial when** — risks or opportunities are identified but not linked to continual improvement
- **unmet when** — no evidence of risks and opportunities determined for continual improvement; only general statements about improvement

### `6.1.1/4` The organization shall establish and maintain AI risk criteria that support distinguishing acceptable from non-acceptable risks

- **subject** — AI risk criteria for distinguishing acceptable from non-acceptable risks
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a document exists that defines criteria for distinguishing acceptable from non-acceptable AI risks
- **partial when** — criteria are defined but not maintained, or only partially distinguish risks
- **unmet when** — no criteria are documented; only general statements about risk acceptability
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Considerations for risk appetite and tolerance from ISO/IEC 38507 and ISO/IEC 23894

### `6.1.1/5` The organization shall establish and maintain AI risk criteria that support performing AI risk assessments

- **subject** — AI risk criteria for performing AI risk assessments
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a document exists that defines criteria to be used in AI risk assessments
- **partial when** — criteria are defined but not maintained, or only partially support risk assessment
- **unmet when** — no criteria are documented; only general statements about risk assessment

### `6.1.1/6` The organization shall establish and maintain AI risk criteria that support conducting AI risk treatment

- **subject** — AI risk criteria for conducting AI risk treatment
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a document exists that defines criteria to guide AI risk treatment decisions
- **partial when** — criteria are defined but not maintained, or only partially support risk treatment
- **unmet when** — no criteria are documented; only general statements about risk treatment

### `6.1.1/7` The organization shall establish and maintain AI risk criteria that support assessing AI risk impacts

- **subject** — AI risk criteria for assessing AI risk impacts
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a document exists that defines criteria for assessing the impacts of AI risks
- **partial when** — criteria are defined but not maintained, or only partially support impact assessment
- **unmet when** — no criteria are documented; only general statements about risk impacts

### `6.1.1/8` The organization shall determine the risks and opportunities according to the domain and application context of an AI system

- **subject** — risks and opportunities based on domain and application context
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows risks and opportunities are determined with explicit reference to the domain and application context of the AI system
- **partial when** — domain or application context is mentioned but not used in determination
- **unmet when** — risks and opportunities are determined without reference to domain or application context

### `6.1.1/9` The organization shall determine the risks and opportunities according to the intended use

- **subject** — risks and opportunities based on intended use
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows risks and opportunities are determined with explicit reference to the intended use of the AI system
- **partial when** — intended use is mentioned but not used in determination
- **unmet when** — risks and opportunities are determined without reference to intended use

### `6.1.1/10` The organization shall determine the risks and opportunities according to the external and internal context described in 4.1

- **subject** — risks and opportunities based on external and internal context from 4.1
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows risks and opportunities are determined with explicit reference to the external and internal context described in clause 4.1
- **partial when** — external or internal context is mentioned but not used in determination
- **unmet when** — risks and opportunities are determined without reference to external and internal context
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - More than one AI system can be considered; determination is performed for each system or grouping

### `6.1.1/11` The organization shall plan actions to address these risks and opportunities

- **subject** — actions planned to address identified risks and opportunities
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process or plan for actions to address the identified risks and opportunities
- **partial when** — actions are listed but no process or plan is described
- **unmet when** — no evidence of planning actions; only identification of risks and opportunities

### `6.1.1/12` The organization shall plan how to integrate and implement the actions into its AI management system processes

- **subject** — integration and implementation of actions into AI management system processes
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how actions to address risks and opportunities are integrated and implemented into AI management system processes
- **partial when** — integration or implementation is mentioned but not described
- **unmet when** — no evidence of integration or implementation planning; only actions listed

### `6.1.1/13` The organization shall plan how to evaluate the effectiveness of these actions

- **subject** — evaluation of effectiveness of actions addressing risks and opportunities
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process or method for evaluating the effectiveness of actions taken to address risks and opportunities
- **partial when** — evaluation is mentioned but no process or method is described
- **unmet when** — no evidence of evaluation planning; only actions listed

### `6.1.1/14` The organization shall retain documented information on actions taken to identify and address AI risks and AI opportunities

- **subject** — documented information on actions taken to identify and address AI risks and opportunities
- **actor** — `organization` · **form** — `record`
- **met when** — a record exists showing actions taken to identify and address AI risks and opportunities
- **partial when** — records exist for actions taken to identify OR address, but not both
- **unmet when** — no records of actions taken; only plans or intentions documented
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Guidance on risk management implementation in ISO/IEC 23894
  - Context and sectoral definitions of risk may impact risk management activities


## 6.1.2 — AI risk assessment

*9 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `6.1.2/0` The organization shall define and establish an AI risk assessment process that is informed by and aligned with the AI policy and AI objectives.

- **subject** — AI risk assessment process alignment with AI policy and AI objectives
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes the AI risk assessment process and explicitly states it is informed by and aligned with the AI policy and AI objectives, referencing both documents or their contents.
- **partial when** — the process is described as aligned with only the AI policy or only the AI objectives, or alignment is stated as an intention without evidence of implementation.
- **unmet when** — the process is described without reference to the AI policy or AI objectives, or only general risk management is discussed without specific mention of AI policy/objectives.

### `6.1.2/1` The organization shall define and establish an AI risk assessment process that is designed such that repeated AI risk assessments can produce consistent, valid and comparable results.

- **subject** — AI risk assessment process design for consistency, validity, and comparability
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes the process design features (e.g., standardized methods, templates, criteria) that ensure repeated assessments yield consistent, valid, and comparable results.
- **partial when** — the process mentions consistency or comparability but lacks detail on how validity is ensured, or vice versa.
- **unmet when** — the process is described without mention of consistency, validity, or comparability, or only a general risk assessment process is described without these features.

### `6.1.2/2` The organization shall define and establish an AI risk assessment process that identifies risks that aid or prevent achieving its AI objectives.

- **subject** — identification of risks relevant to achieving AI objectives
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how the process identifies risks that could either support or hinder the achievement of the organization's AI objectives.
- **partial when** — the process describes identification of risks but only those that prevent achieving objectives, or only those that aid, not both.
- **unmet when** — the process describes risk identification in general terms without reference to AI objectives, or only identifies risks unrelated to AI objectives.

### `6.1.2/3` The organization shall define and establish an AI risk assessment process that analyses the AI risks to assess the potential consequences to the organization, individuals and societies that would result if the identified risks were to materialize.

- **subject** — analysis of AI risks for potential consequences to organization, individuals, and societies
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes the process for analyzing AI risks, specifically assessing potential consequences to the organization, individuals, and societies if risks materialize.
- **partial when** — the process describes assessment of consequences to only the organization, or only individuals, or only societies, not all three.
- **unmet when** — the process describes risk analysis without assessing consequences, or only assesses consequences for unrelated entities.
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - AI system impact assessment may be used for consequence assessment.

### `6.1.2/4` The organization shall define and establish an AI risk assessment process that analyses the AI risks to assess, where applicable, the realistic likelihood of the identified risks.

- **subject** — analysis of AI risks for realistic likelihood
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes the process for analyzing AI risks, including assessment of the realistic likelihood of identified risks where applicable.
- **partial when** — the process describes likelihood assessment but does not specify it is realistic or only applies it to some risks without justification.
- **unmet when** — the process omits likelihood assessment or only discusses likelihood in general terms without application to identified AI risks.

### `6.1.2/5` The organization shall define and establish an AI risk assessment process that analyses the AI risks to determine the levels of risk.

- **subject** — analysis of AI risks to determine risk levels
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes the process for analyzing AI risks and determining their levels (e.g., low, medium, high, or other scale).
- **partial when** — the process describes determination of risk levels for only some risks or only in general terms without a defined scale.
- **unmet when** — the process omits determination of risk levels or only describes risk analysis without assigning levels.

### `6.1.2/6` The organization shall define and establish an AI risk assessment process that evaluates the AI risks to compare the results of the risk analysis with the risk criteria.

- **subject** — evaluation of AI risks by comparison with risk criteria
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes the process for evaluating AI risks, specifically comparing risk analysis results with defined risk criteria (see 6.1.1).
- **partial when** — the process describes comparison with risk criteria but lacks detail on how the criteria are applied or only applies to some risks.
- **unmet when** — the process omits comparison with risk criteria or only describes evaluation in general terms without reference to risk criteria.

### `6.1.2/7` The organization shall define and establish an AI risk assessment process that evaluates the AI risks to prioritize the assessed risks for risk treatment.

- **subject** — evaluation of AI risks for prioritization for risk treatment
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes the process for evaluating AI risks and prioritizing them for risk treatment based on assessment results.
- **partial when** — the process describes prioritization but only for some risks or lacks detail on how prioritization is determined.
- **unmet when** — the process omits prioritization or only describes risk evaluation without prioritization for treatment.

### `6.1.2/8` The organization shall retain documented information about the AI risk assessment process.

- **subject** — documented information about the AI risk assessment process
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage states that documented information about the AI risk assessment process exists, such as a procedure, policy, or process description.
- **partial when** — a passage states an intention to retain documented information or references a draft or incomplete document.
- **unmet when** — no documented information is referenced, or only undocumented practices or oral descriptions are provided.


## 6.1.3 — AI risk treatment

*13 requirements · Annex A: all of Annex A (selection / implementation rule)*

### `6.1.3/0` The organization shall define an AI risk treatment process to select appropriate AI risk treatment options.

- **subject** — selection of AI risk treatment options
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a defined, repeatable process for selecting AI risk treatment options based on risk assessment results
- **partial when** — a process is described but lacks detail on how options are selected or only covers some types of risks
- **unmet when** — only a list of options is provided without a process, or a process for non-AI risks is described

### `6.1.3/1` The organization shall define an AI risk treatment process to determine all controls that are necessary to implement the AI risk treatment options chosen and compare the controls with those in Annex A to verify that no necessary controls have been omitted.

- **subject** — determination and comparison of necessary controls for AI risk treatment options
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process for identifying necessary controls for chosen AI risk treatment options and comparing them with Annex A controls to ensure completeness
- **partial when** — the process describes determination of controls but omits comparison with Annex A, or vice versa
- **unmet when** — only a list of controls is provided without a process, or comparison is made to controls outside Annex A
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Annex A provides reference controls for meeting organizational objectives and addressing risks related to the design and use of AI systems.

### `6.1.3/2` The organization shall define an AI risk treatment process to consider the controls from Annex A that are relevant for the implementation of the AI risk treatment options.

- **subject** — consideration of relevant Annex A controls for AI risk treatment
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process for reviewing Annex A controls to determine their relevance to the implementation of selected AI risk treatment options
- **partial when** — the process mentions Annex A controls but does not specify how relevance is determined
- **unmet when** — controls from sources other than Annex A are considered without reference to Annex A, or only a list of controls is given

### `6.1.3/3` The organization shall define an AI risk treatment process to identify if additional controls are necessary beyond those in Annex A in order to implement all risk treatment options.

- **subject** — identification of additional controls beyond Annex A for AI risk treatment
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process for identifying when controls beyond those listed in Annex A are needed to implement all risk treatment options
- **partial when** — the process identifies additional controls but does not specify how the need is determined
- **unmet when** — only Annex A controls are considered, or additional controls are listed without a process for identification
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Annex A controls are not exhaustive and additional control objectives and controls can be needed.

### `6.1.3/4` The organization shall define an AI risk treatment process to consider the guidance in Annex B for the implementation of controls determined in b) and c).

- **subject** — consideration of Annex B guidance for implementing controls
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process for consulting Annex B guidance when implementing controls determined in b) and c)
- **partial when** — Annex B is referenced but not integrated into the process, or only some controls are considered
- **unmet when** — Annex B guidance is not mentioned, or guidance from other sources is used instead

### `6.1.3/5` The organization shall produce a statement of applicability that contains the necessary controls [see b), c) and d)] and provide justification for inclusion and exclusion of controls.

- **subject** — statement of applicability for necessary controls with justification
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a document exists listing necessary controls, with explicit justification for each control's inclusion or exclusion
- **partial when** — the statement lists controls but lacks justification for inclusion or exclusion, or only covers some controls
- **unmet when** — a statement of applicability is referenced but not provided, or justification is missing entirely
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - The organization can provide documented justifications for excluding any control objectives in general or for specific AI systems, whether those listed in Annex A or established by the organization itself.

### `6.1.3/6` The organization shall formulate an AI risk treatment plan.

- **subject** — AI risk treatment plan
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a document exists that details the AI risk treatment plan, including actions, timelines, responsible parties, and controls
- **partial when** — a draft plan exists or only some elements (e.g., actions or controls) are documented
- **unmet when** — only a reference to a plan is provided, or a plan for non-AI risks is documented

### `6.1.3/7` The organization shall obtain approval from the designated management for the AI risk treatment plan and for acceptance of the residual AI risks.

- **subject** — approval of AI risk treatment plan and acceptance of residual AI risks
- **actor** — `organization` · **form** — `record`
- **met when** — a record exists showing designated management has approved the AI risk treatment plan and accepted residual AI risks
- **partial when** — approval is documented for the plan but not for residual risks, or vice versa
- **unmet when** — only an intention to seek approval is stated, or approval is from an incorrect authority

### `6.1.3/8` The necessary controls shall be aligned to the objectives in 6.2.

- **subject** — alignment of necessary controls to objectives in 6.2
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage demonstrates that necessary controls are mapped or linked to the objectives specified in clause 6.2
- **partial when** — alignment is shown for some controls or some objectives, but not all
- **unmet when** — controls are listed without reference to objectives, or objectives from another clause are used

### `6.1.3/9` The necessary controls shall be available as documented information.

- **subject** — necessary controls for AI risk treatment
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a document exists listing all necessary controls for AI risk treatment
- **partial when** — only some controls are documented, or a draft document exists
- **unmet when** — controls are referenced but not documented, or only controls for non-AI risks are documented

### `6.1.3/10` The necessary controls shall be communicated within the organization.

- **subject** — communication of necessary controls for AI risk treatment
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that necessary controls have been communicated internally (e.g., via training, publication, meetings)
- **partial when** — an intention to communicate is stated, or only some controls are communicated
- **unmet when** — communication is about controls for non-AI risks, or only a procedure for communication exists without evidence it happened

### `6.1.3/11` The necessary controls shall be available to interested parties, as appropriate.

- **subject** — availability of necessary controls to interested parties
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that necessary controls are made available to relevant interested parties (e.g., external stakeholders, regulators), as appropriate
- **partial when** — controls are available to some interested parties but not all relevant ones, or only an intention to make them available is stated
- **unmet when** — controls are not made available, or only internal communication is evidenced

### `6.1.3/12` The organization shall retain documented information about the AI risk treatment process.

- **subject** — AI risk treatment process
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a document exists describing the AI risk treatment process, including its steps and criteria
- **partial when** — only a draft or partial process is documented, or only some steps are described
- **unmet when** — the process is referenced but not documented, or documentation is about a non-AI risk treatment process


## 6.1.4 — AI system impact assessment

*6 requirements · Annex A: A.5.2, A.5.3, A.5.4, A.5.5*

### `6.1.4/0` The organization shall define a process for assessing the potential consequences for individuals or groups of individuals, or both, and societies that can result from the development, provision or use of AI systems.

- **subject** — assessment of potential consequences for individuals, groups, and societies from AI system development, provision, or use
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a defined, repeatable process for assessing potential consequences for individuals, groups, and societies arising from the development, provision, or use of AI systems
- **partial when** — the process is described for only one aspect (e.g., development but not provision or use), or only for individuals but not groups or societies
- **unmet when** — a passage describes a responsibility to assess consequences but no process, or describes a process for a different type of assessment (e.g., risk assessment only), or references an unseen process
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - discipline-specific impact assessments (e.g. safety, privacy, security) may be required in some contexts

### `6.1.4/1` The AI system impact assessment shall determine the potential consequences an AI system’s deployment, intended use and foreseeable misuse has on individuals or groups of individuals, or both, and societies.

- **subject** — potential consequences of AI system deployment, intended use, and foreseeable misuse on individuals, groups, and societies
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows that the impact assessment determines the potential consequences of deployment, intended use, and foreseeable misuse of the AI system for individuals, groups, and societies
- **partial when** — the determination covers only deployment or intended use, but not foreseeable misuse, or only individuals but not groups or societies
- **unmet when** — a passage describes only the process for assessment, or only identifies risks without determining consequences, or references an unseen determination
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - discipline-specific impact assessments (e.g. safety, privacy, security) may be required in some contexts

### `6.1.4/2` The AI system impact assessment shall take into account the specific technical and societal context where the AI system is deployed and applicable jurisdictions.

- **subject** — technical and societal context and applicable jurisdictions for AI system deployment
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows that the impact assessment considers the technical context, societal context, and applicable jurisdictions where the AI system is deployed
- **partial when** — the assessment considers only technical context or only societal context or only jurisdictions, but not all
- **unmet when** — a passage describes context consideration for a different process, or only references context without showing it is taken into account in the impact assessment
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - discipline-specific impact assessments (e.g. safety, privacy, security) may be required in some contexts

### `6.1.4/3` The result of the AI system impact assessment shall be documented.

- **subject** — result of the AI system impact assessment
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage evidences that the result of the AI system impact assessment is documented (e.g., in a report, record, or other document)
- **partial when** — the result is documented for only part of the assessment (e.g., only for deployment, not for intended use or misuse)
- **unmet when** — a passage describes the process or determination but does not document the result, or references an unseen document

### `6.1.4/4` Where appropriate, the result of the system impact assessment can be made available to relevant interested parties as defined by the organization.

- **subject** — availability of the AI system impact assessment result to relevant interested parties
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the result of the impact assessment was made available to relevant interested parties, as defined by the organization, where appropriate
- **partial when** — a passage states an intention to make the result available but does not evidence it actually happened, or only some relevant parties received it
- **unmet when** — a passage describes availability for a different assessment, or only references the possibility without evidence of actual availability

### `6.1.4/5` The organization shall consider the results of the AI system impact assessment in the risk assessment (see 6.1.2).

- **subject** — consideration of AI system impact assessment results in the risk assessment
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the results of the AI system impact assessment were considered in the risk assessment process
- **partial when** — a passage states an intention to consider the results but does not evidence it actually happened, or only some results were considered
- **unmet when** — a passage describes consideration of results in a different process, or only references the risk assessment without showing the impact assessment results were considered
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - discipline-specific impact assessments (e.g. safety, privacy, security) may be required in some contexts


## 6.2 — AI objectives and planning to achieve them

*13 requirements · Annex A: A.6.1.2, A.6.1.3, A.9.3*

### `6.2/0` The organization shall establish AI objectives at relevant functions and levels.

- **subject** — AI objectives at relevant functions and levels
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies specific AI objectives and shows they are set for relevant functions and levels within the organization
- **partial when** — AI objectives are established for some functions or levels, but not all relevant ones
- **unmet when** — no AI objectives are established, or objectives are set only at the top level with no evidence for other relevant functions/levels

### `6.2/1` AI objectives shall be consistent with the AI policy.

- **subject** — consistency between AI objectives and the AI policy
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage demonstrates that the AI objectives align with the stated AI policy, referencing both and showing their relationship
- **partial when** — some objectives are shown to be consistent, but others are not addressed or are ambiguous
- **unmet when** — objectives are stated without reference to the AI policy, or objectives contradict the AI policy

### `6.2/2` AI objectives shall be measurable (if practicable).

- **subject** — measurability of AI objectives
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows that AI objectives include measurable criteria or metrics, or explains why measurement is not practicable
- **partial when** — some objectives are measurable, others lack metrics or justification for non-measurability
- **unmet when** — objectives are stated without any reference to measurement or practicability

### `6.2/3` AI objectives shall take into account applicable requirements.

- **subject** — applicable requirements considered in AI objectives
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage shows that AI objectives are set with reference to applicable legal, regulatory, contractual, or stakeholder requirements
- **partial when** — only some applicable requirements are considered, or requirements are referenced but not integrated into objectives
- **unmet when** — objectives are set without any reference to applicable requirements

### `6.2/4` AI objectives shall be monitored.

- **subject** — monitoring of AI objectives
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process or method for monitoring progress toward AI objectives
- **partial when** — monitoring is described for some objectives, or monitoring is planned but not implemented
- **unmet when** — no monitoring process is described, or monitoring is referenced only for non-AI objectives

### `6.2/5` AI objectives shall be communicated.

- **subject** — communication of AI objectives
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how AI objectives are communicated to relevant stakeholders, functions, or levels
- **partial when** — communication is described for some objectives or some stakeholders, or only an intention to communicate is stated
- **unmet when** — no communication process is described, or communication is referenced only for non-AI objectives

### `6.2/6` AI objectives shall be updated as appropriate.

- **subject** — updating of AI objectives
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process for reviewing and updating AI objectives when necessary
- **partial when** — updating is described for some objectives, or only an intention to update is stated
- **unmet when** — no updating process is described, or updating is referenced only for non-AI objectives

### `6.2/7` AI objectives shall be available as documented information.

- **subject** — documented information about AI objectives
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage evidences the existence of documented information listing the AI objectives
- **partial when** — documented information exists for some objectives, but not all
- **unmet when** — no documented information about AI objectives is available, or only a reference to an unseen document is provided

### `6.2/8` When planning how to achieve its AI objectives, the organization shall determine what will be done.

- **subject** — actions to achieve AI objectives
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage specifies the actions, tasks, or steps that will be taken to achieve each AI objective
- **partial when** — actions are determined for some objectives, but not all
- **unmet when** — no actions are determined, or only general intentions are stated without specifics

### `6.2/9` When planning how to achieve its AI objectives, the organization shall determine what resources will be required.

- **subject** — resources required to achieve AI objectives
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies the resources (personnel, technology, budget, etc.) needed for each AI objective
- **partial when** — resources are determined for some objectives, but not all
- **unmet when** — no resources are determined, or only general statements about resource needs are made

### `6.2/10` When planning how to achieve its AI objectives, the organization shall determine who will be responsible.

- **subject** — responsibility for achieving AI objectives
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage assigns responsibility for achieving each AI objective to specific roles or individuals
- **partial when** — responsibility is assigned for some objectives, but not all
- **unmet when** — no responsibility is assigned, or only general statements about responsibility are made

### `6.2/11` When planning how to achieve its AI objectives, the organization shall determine when it will be completed.

- **subject** — completion timelines for AI objectives
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage specifies completion dates or timelines for each AI objective
- **partial when** — timelines are determined for some objectives, but not all
- **unmet when** — no completion timelines are determined, or only general statements about timing are made

### `6.2/12` When planning how to achieve its AI objectives, the organization shall determine how the results will be evaluated.

- **subject** — evaluation of results for AI objectives
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage describes the criteria or methods for evaluating whether AI objectives have been achieved
- **partial when** — evaluation methods are determined for some objectives, but not all
- **unmet when** — no evaluation methods are determined, or only general statements about evaluation are made
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Annex C: risk management objectives
  - A.6.1 and A.9.3: control objectives and controls for responsible development and use of AI systems
  - B.6.1 and B.9.3: implementation guidance for controls


## 6.3 — Planning of changes

*1 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `6.3/0` Changes to the AI management system are carried out in a planned manner when the organization determines the need for changes.

- **subject** — changes to the AI management system
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a defined, repeatable process for planning and implementing changes to the AI management system, including steps or criteria for planning such changes when a need is determined
- **partial when** — a passage describes an intention to plan changes or references planning without detailing a process, or only describes planning for some types of changes but not all
- **unmet when** — a passage describes changes being made without any reference to planning, or only describes who is responsible for changes without describing a process, or references a process for planning changes to a different management system (e.g., quality or information security) instead of the AI management system


## 7.1 — Resources

*2 requirements · Annex A: A.4.2, A.4.3, A.4.4, A.4.5, A.4.6*

### `7.1/0` The organization shall determine the resources needed for the establishment, implementation, maintenance and continual improvement of the AI management system.

- **subject** — resources needed for the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage describes how the organization identifies or assesses the resources required for establishing, implementing, maintaining, and continually improving the AI management system (e.g., personnel, infrastructure, technology, financial resources, etc.)
- **partial when** — a passage describes determination of resources for only some aspects (e.g., only establishment or only implementation), or only for part of the AI management system
- **unmet when** — a passage describes provision of resources without evidence of determination, or determination of resources for a different management system (e.g., quality, information security), or references an unseen artefact
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Control objectives and controls for AI resources are provided in A.4 in Table A.1. Implementation guidance for these controls is provided in Clause B.4.

### `7.1/1` The organization shall provide the resources needed for the establishment, implementation, maintenance and continual improvement of the AI management system.

- **subject** — provision of resources for the AI management system
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the organization has allocated or made available the resources identified as needed for the AI management system (e.g., budget allocation, staff assignment, procurement records, infrastructure deployment)
- **partial when** — a passage evidences provision of resources for only some aspects (e.g., only establishment or only implementation), or only for part of the AI management system
- **unmet when** — a passage describes an intention to provide resources without evidence of actual provision, or provision of resources for a different management system, or references an unseen artefact
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Control objectives and controls for AI resources are provided in A.4 in Table A.1. Implementation guidance for these controls is provided in Clause B.4.


## 7.2 — Competence

*4 requirements · Annex A: none — guidance B.4.6 only*

### `7.2/0` Determine the necessary competence of person(s) doing work under its control that affects its AI performance

- **subject** — necessary competence for persons affecting AI performance
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies the specific competence (knowledge, skills, abilities) required for roles or tasks that impact AI performance, and shows how these requirements were determined
- **partial when** — only some roles or tasks are covered, or competence is described in general terms without linking to AI performance
- **unmet when** — no determination of competence is shown; only a statement of responsibility or a generic HR policy; competence for unrelated roles (not affecting AI performance)
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Implementation guidance for human resources including consideration of necessary expertise is provided in B.4.6.

### `7.2/1` Ensure that these persons are competent on the basis of appropriate education, training or experience

- **subject** — ensuring competence of persons affecting AI performance
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process or method for verifying that persons in relevant roles have the required competence, referencing education, training, or experience
- **partial when** — a process is described but only for some relevant persons, or only one aspect (education, training, or experience) is considered
- **unmet when** — no process for ensuring competence is described; only a statement of required competence without verification; process for unrelated roles
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Implementation guidance for human resources including consideration of necessary expertise is provided in B.4.6.

### `7.2/2` Where applicable, take actions to acquire the necessary competence, and evaluate the effectiveness of the actions taken

- **subject** — actions to acquire competence and evaluation of their effectiveness
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes actions taken (such as training, mentoring, reassignment, hiring, or contracting) to acquire necessary competence, and explains how the effectiveness of these actions is evaluated
- **partial when** — actions are described but no evaluation of effectiveness, or only some actions are covered
- **unmet when** — no actions or evaluation are described; only an intention to take action; actions for unrelated competence
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Applicable actions can include, for example: the provision of training to, the mentoring of, or the re-assignment of currently employed persons; or the hiring or contracting of competent persons.

### `7.2/3` Appropriate documented information shall be available as evidence of competence

- **subject** — evidence of competence for persons affecting AI performance
- **actor** — `organization` · **form** — `record`
- **met when** — a passage references or presents documented information (such as certificates, training records, experience logs, or qualification documents) that evidences the competence of persons in relevant roles
- **partial when** — evidence is available for only some relevant persons or only some aspects of competence
- **unmet when** — no documented evidence is available; only a process or policy is described; evidence for unrelated roles


## 7.3 — Awareness

*3 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `7.3/0` Persons doing work under the organization’s control shall be aware of the AI policy (see 5.2)

- **subject** — awareness of the AI policy by persons under the organization's control
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that persons under the organization's control have been made aware of the AI policy, such as attendance records for policy briefings, signed attestations, training completion records, or documented acknowledgements specifically referencing the AI policy
- **partial when** — a statement of intent to make persons aware of the AI policy, or evidence that only some relevant persons have been made aware, or evidence that only future hires will be made aware
- **unmet when** — no evidence of awareness of the AI policy by persons under the organization's control; evidence relates to awareness of a different policy; evidence only describes the policy without showing awareness by persons

### `7.3/1` Persons doing work under the organization’s control shall be aware of their contribution to the effectiveness of the AI management system, including the benefits of improved AI performance

- **subject** — awareness by persons under the organization's control of their contribution to the effectiveness of the AI management system and the benefits of improved AI performance
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that persons under the organization's control have been made aware of how their actions contribute to the effectiveness of the AI management system and the benefits of improved AI performance, such as training records, communication materials, or documented acknowledgements referencing these points
- **partial when** — a statement of intent to make persons aware, or evidence that only some persons have been made aware, or evidence that only one aspect (contribution or benefits) has been covered
- **unmet when** — no evidence of awareness of contribution or benefits; evidence relates to general AI awareness without reference to contribution or benefits; evidence only describes the management system without showing awareness by persons

### `7.3/2` Persons doing work under the organization’s control shall be aware of the implications of not conforming with the AI management system requirements

- **subject** — awareness by persons under the organization's control of the implications of not conforming with AI management system requirements
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that persons under the organization's control have been made aware of the consequences or implications of not conforming with AI management system requirements, such as training materials, communication records, or documented acknowledgements referencing these implications
- **partial when** — a statement of intent to make persons aware, or evidence that only some persons have been made aware, or evidence that only future hires will be made aware
- **unmet when** — no evidence of awareness of implications; evidence relates to general AI management system requirements without reference to implications; evidence only describes the requirements without showing awareness by persons


## 7.4 — Communication

*4 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `7.4/0` The organization shall determine what it will communicate relevant to the AI management system

- **subject** — the content of communications relevant to the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies specific topics, messages, or information to be communicated internally or externally about the AI management system
- **partial when** — only some relevant communication topics are identified, or a general intention to communicate is stated without specifying what will be communicated
- **unmet when** — no determination of communication content is present, or the passage only describes communication about unrelated management systems or policies

### `7.4/1` The organization shall determine when to communicate relevant to the AI management system

- **subject** — timing or frequency of communications relevant to the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage specifies the timing, frequency, or triggers for communications (e.g., regular updates, upon changes, at project milestones) about the AI management system
- **partial when** — only some communication timings are specified, or a general statement about communicating 'as needed' without further detail
- **unmet when** — no determination of communication timing is present, or the passage only describes timing for unrelated communications

### `7.4/2` The organization shall determine with whom to communicate relevant to the AI management system

- **subject** — audiences or recipients of communications relevant to the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies specific internal or external parties, groups, or roles to receive communications about the AI management system
- **partial when** — only some relevant recipients are identified, or a general statement about communicating with 'stakeholders' without specifying who
- **unmet when** — no determination of communication recipients is present, or the passage only describes recipients for unrelated communications

### `7.4/3` The organization shall determine how to communicate relevant to the AI management system

- **subject** — methods or channels for communications relevant to the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage specifies the means, methods, or channels (e.g., email, meetings, intranet, reports) used for communicating about the AI management system
- **partial when** — only some communication methods are specified, or a general statement about using 'appropriate channels' without further detail
- **unmet when** — no determination of communication methods is present, or the passage only describes methods for unrelated communications


## 7.5.1 — Documented information - General

*2 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `7.5.1/0` The organization’s AI management system includes documented information required by ISO/IEC 42001:2023

- **subject** — documented information required by ISO/IEC 42001:2023
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage lists or presents documents explicitly required by ISO/IEC 42001:2023 (e.g., AI policy, risk assessment, objectives, procedures, records), showing they are included in the AI management system
- **partial when** — only some required documents are listed or presented, or there is an intention to include them but not evidence of their existence
- **unmet when** — no evidence of required documents being included, or only documents required by other standards or policies are referenced, or a cross-reference to an unseen artefact is given
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - The extent of documented information can differ due to organization size, activities, process complexity, and competence

### `7.5.1/1` The organization’s AI management system includes documented information determined by the organization as necessary for its effectiveness

- **subject** — documented information determined by the organization as necessary for the effectiveness of the AI management system
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage lists or presents documents that the organization has decided are necessary for the effectiveness of its AI management system, such as additional procedures, guidelines, or records beyond those required by the standard
- **partial when** — only some necessary documents are listed or presented, or there is an intention to include them but not evidence of their existence
- **unmet when** — no evidence of organization-determined necessary documents being included, or only required documents are referenced with no mention of additional necessary ones, or a cross-reference to an unseen artefact is given
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - The extent of documented information can differ due to organization size, activities, process complexity, and competence


## 7.5.2 — Creating and updating documented information

*3 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `7.5.2/0` When creating and updating documented information, the organization shall ensure appropriate identification and description (e.g. a title, date, author or reference number)

- **subject** — identification and description of documented information
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process or procedure that ensures all documented information is assigned appropriate identification and description, such as title, date, author, or reference number, whenever it is created or updated
- **partial when** — the process is described for only some types of documented information, or only some elements (e.g. title but not date or author) are ensured
- **unmet when** — no process is described for identification and description, or the process is for a different type of information (e.g. records, not documented information), or only a responsibility is assigned without a defined process

### `7.5.2/1` When creating and updating documented information, the organization shall ensure appropriate format (e.g. language, software version, graphics) and media (e.g. paper, electronic)

- **subject** — format and media of documented information
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process or procedure that ensures all documented information is created and updated in appropriate formats (such as language, software version, graphics) and media (such as paper or electronic), with criteria or controls specified
- **partial when** — the process is described for only format or only media, or only for some types of documented information
- **unmet when** — no process is described for format and media, or the process is for a different type of information, or only a responsibility is assigned without a defined process

### `7.5.2/2` When creating and updating documented information, the organization shall ensure appropriate review and approval for suitability and adequacy

- **subject** — review and approval of documented information for suitability and adequacy
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process or procedure that ensures all documented information is reviewed and approved for suitability and adequacy before it is finalized or updated, including criteria for review and approval
- **partial when** — the process is described for only review or only approval, or only for some types of documented information
- **unmet when** — no process is described for review and approval, or the process is for a different type of information, or only a responsibility is assigned without a defined process


## 7.5.3 — Control of documented information

*7 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `7.5.3/0` Documented information required by the AI management system and by this document shall be controlled to ensure it is available and suitable for use, where and when it is needed

- **subject** — control of documented information required by the AI management system and ISO/IEC 42001:2023
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process or mechanism ensuring that documented information required by the AI management system and ISO/IEC 42001:2023 is available and suitable for use at the necessary locations and times
- **partial when** — the process is described for only some types of documented information, or only for availability but not suitability, or only for some locations/times
- **unmet when** — a passage describes availability or suitability for documented information NOT required by the AI management system or this document, or only states a responsibility without describing a process

### `7.5.3/1` Documented information required by the AI management system and by this document shall be controlled to ensure it is adequately protected (e.g. from loss of confidentiality, improper use or loss of integrity)

- **subject** — protection of documented information required by the AI management system and ISO/IEC 42001:2023
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process or mechanism ensuring adequate protection of documented information required by the AI management system and ISO/IEC 42001:2023, including protection from loss of confidentiality, improper use, or loss of integrity
- **partial when** — the process is described for only some types of protection (e.g. only confidentiality, not integrity), or only for some documented information
- **unmet when** — a passage describes protection for documented information NOT required by the AI management system or this document, or only states a responsibility without describing a process

### `7.5.3/2` The organization shall address distribution, access, retrieval and use of documented information, as applicable

- **subject** — distribution, access, retrieval and use of documented information
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how the organization manages distribution, access, retrieval, and use of documented information, including any controls or procedures
- **partial when** — only some activities (e.g. only access and retrieval) are described, or only some types of documented information are covered
- **unmet when** — a passage describes distribution, access, retrieval, or use for information NOT considered documented information, or only states a responsibility without describing a process
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Access can imply a decision regarding the permission to view the documented information only, or the permission and authority to view and change the documented information.

### `7.5.3/3` The organization shall address storage and preservation, including preservation of legibility, of documented information, as applicable

- **subject** — storage and preservation of documented information, including legibility
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how the organization manages storage and preservation of documented information, including measures to preserve legibility
- **partial when** — only storage or only preservation (not both) is described, or only some types of documented information are covered
- **unmet when** — a passage describes storage or preservation for information NOT considered documented information, or only states a responsibility without describing a process

### `7.5.3/4` The organization shall address control of changes (e.g. version control) of documented information, as applicable

- **subject** — control of changes to documented information, including version control
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how the organization manages changes to documented information, including version control or similar mechanisms
- **partial when** — only some aspects of change control (e.g. only version control, not approval of changes) are described, or only some types of documented information are covered
- **unmet when** — a passage describes change control for information NOT considered documented information, or only states a responsibility without describing a process

### `7.5.3/5` The organization shall address retention and disposition of documented information, as applicable

- **subject** — retention and disposition of documented information
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how the organization manages retention and disposition of documented information, including retention periods and disposal methods
- **partial when** — only retention or only disposition (not both) is described, or only some types of documented information are covered
- **unmet when** — a passage describes retention or disposition for information NOT considered documented information, or only states a responsibility without describing a process

### `7.5.3/6` Documented information of external origin determined by the organization to be necessary for the planning and operation of the AI management system shall be identified as appropriate and controlled

- **subject** — identification and control of documented information of external origin necessary for the AI management system
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how the organization identifies and controls documented information of external origin that is necessary for the planning and operation of the AI management system
- **partial when** — only identification or only control (not both) is described, or only some types of external documented information are covered
- **unmet when** — a passage describes identification or control for external information NOT determined as necessary for the AI management system, or only states a responsibility without describing a process


## 8.1 — Operational planning and control

*8 requirements · Annex A: all of Annex A (selection / implementation rule)*

### `8.1/0` The organization shall plan, implement and control the processes needed to meet requirements, and to implement the actions determined in Clause 6.

- **subject** — operational planning, implementation and control of processes needed to meet requirements and implement actions from Clause 6
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a defined, repeatable process for planning, implementing, and controlling processes to meet requirements and actions from Clause 6
- **partial when** — only planning or only implementation or only control is described, or the process is described for some but not all requirements/actions from Clause 6
- **unmet when** — a passage describes unrelated processes, or only assigns responsibility without describing a process, or references an unseen process

### `8.1/1` The organization shall establish criteria for the processes.

- **subject** — criteria for operational processes
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage specifies the criteria used to judge or control operational processes
- **partial when** — criteria are stated for some but not all processes, or criteria are described in general terms without specifics
- **unmet when** — criteria are not mentioned, or only a process is described without criteria, or criteria are referenced but not shown

### `8.1/2` The organization shall implement control of the processes in accordance with the criteria.

- **subject** — control of operational processes according to established criteria
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how operational processes are controlled in line with the established criteria
- **partial when** — controls are described for some but not all processes, or controls are described but not linked to criteria
- **unmet when** — controls are described without reference to criteria, or only criteria are described without controls, or controls are referenced but not shown

### `8.1/3` The organization shall implement the controls determined according to 6.1.3 that are related to the operation of the AI management system.

- **subject** — implementation of controls from 6.1.3 related to AI management system operation
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes how controls determined in 6.1.3 are implemented in the operation of the AI management system
- **partial when** — controls from 6.1.3 are implemented for some but not all relevant operations, or implementation is described in general terms without specifics
- **unmet when** — controls from 6.1.3 are not mentioned, or only referenced without evidence of implementation, or controls are described for unrelated systems
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Annex A lists reference controls and Annex B provides implementation guidance for them.

### `8.1/4` The effectiveness of these controls shall be monitored and corrective actions shall be considered if the intended results are not achieved.

- **subject** — monitoring effectiveness of controls and considering corrective actions
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process for monitoring the effectiveness of controls and considering corrective actions when results are not achieved
- **partial when** — monitoring is described but not corrective actions, or corrective actions are described but not monitoring, or only some controls are covered
- **unmet when** — no process for monitoring or corrective actions is described, or only responsibility is assigned, or only references to monitoring/corrective actions without evidence
- **look for** *(informative, from the standard's NOTES — no verdict of their own)*
  - Annex A lists reference controls and Annex B provides implementation guidance for them.

### `8.1/5` Documented information shall be available to the extent necessary to have confidence that the processes have been carried out as planned.

- **subject** — evidence that operational processes have been carried out as planned
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage provides or describes documented information that shows operational processes were carried out as planned
- **partial when** — documented information is available for some but not all processes, or only partial evidence is provided
- **unmet when** — no documented information is available, or only references to documentation without evidence, or documentation is about unrelated processes

### `8.1/6` The organization shall control planned changes and review the consequences of unintended changes, taking action to mitigate any adverse effects, as necessary.

- **subject** — control of planned changes and review/mitigation of unintended changes in operational processes
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process for controlling planned changes, reviewing unintended changes, and taking action to mitigate adverse effects
- **partial when** — only planned changes are controlled, or only unintended changes are reviewed, or mitigation actions are described for some but not all adverse effects
- **unmet when** — no process for controlling changes or reviewing consequences is described, or only responsibility is assigned, or only references to change control without evidence

### `8.1/7` The organization shall ensure that externally provided processes, products or services that are relevant to the AI management system are controlled.

- **subject** — control of externally provided processes, products or services relevant to the AI management system
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process for controlling externally provided processes, products or services relevant to the AI management system
- **partial when** — controls are described for some but not all externally provided items, or only general statements about control without specifics
- **unmet when** — no process for controlling externally provided items is described, or only responsibility is assigned, or only references to control without evidence


## 8.2 — AI risk assessment (operation)

*2 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `8.2/0` AI risk assessments are performed in accordance with 6.1.2 at planned intervals or when significant changes are proposed or occur

- **subject** — AI risk assessments performed - NOT risk assessments for other systems or processes
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that AI risk assessments have actually been carried out, showing they follow the process described in 6.1.2, and that they occur either at planned intervals or in response to significant changes
- **partial when** — a passage shows AI risk assessments are planned or intended, but does not evidence they have actually been performed; or only some assessments are evidenced (e.g., only at planned intervals, not when changes occur)
- **unmet when** — a passage describes a process for risk assessment but does not evidence actual performance; or references risk assessments for non-AI systems; or only cross-references an unseen artefact

### `8.2/1` The organization retains documented information of the results of all AI risk assessments

- **subject** — results of AI risk assessments - NOT the process or plan, but the actual outcomes
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage evidences that documented information exists and is retained about the results of every AI risk assessment performed
- **partial when** — a passage evidences retention of documented information for only some AI risk assessments, or states an intention to retain but does not show actual retention
- **unmet when** — a passage describes the process or procedure for risk assessment but does not evidence retention of results; or references retention of results for non-AI risk assessments; or only cross-references an unseen artefact


## 8.3 — AI risk treatment (operation)

*4 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `8.3/0` The organization shall implement the AI risk treatment plan according to 6.1.3 and verify its effectiveness.

- **subject** — implementation and verification of the AI risk treatment plan as specified in 6.1.3
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the AI risk treatment plan has been put into operation and that its effectiveness has been checked (e.g., through monitoring, testing, review, or evaluation of outcomes)
- **partial when** — a passage shows the plan was implemented but does not show verification of effectiveness, or vice versa
- **unmet when** — a passage only describes the plan or its intended implementation, or only references 6.1.3 without evidence of action; evidence of implementation or verification for a different plan is inadmissible

### `8.3/1` When risk assessments identify new risks that require treatment, a risk treatment process in accordance with 6.1.3 shall be performed for these risks.

- **subject** — performance of the risk treatment process for newly identified risks, in accordance with 6.1.3
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that, when new risks are identified by risk assessments, the risk treatment process (as defined in 6.1.3) is carried out for those risks
- **partial when** — a passage shows the process was initiated for some new risks but not all, or only describes an intention to perform the process
- **unmet when** — a passage only describes the identification of new risks without evidence of treatment, or describes treatment for risks not newly identified, or references the process without evidence it was performed

### `8.3/2` When risk treatment options as defined by the risk treatment plan are not effective, these treatment options shall be reviewed and revalidated following the risk treatment process according to 6.1.3 and the risk treatment plan shall be updated.

- **subject** — review, revalidation, and updating of risk treatment options and the risk treatment plan when options are found ineffective
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that ineffective risk treatment options are reviewed and revalidated using the process in 6.1.3, and that the risk treatment plan is updated accordingly
- **partial when** — a passage shows review or revalidation occurred but not updating of the plan, or vice versa; or only some ineffective options are addressed
- **unmet when** — a passage only describes the identification of ineffective options without evidence of review, revalidation, or updating; or references the process or plan without evidence of action

### `8.3/3` The organization shall retain documented information of the results of all AI risk treatments.

- **subject** — results of all AI risk treatments
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage evidences that documented information exists and is retained about the results of every AI risk treatment performed
- **partial when** — a passage shows documented information is retained for some but not all AI risk treatments, or only describes an intention to retain such information
- **unmet when** — a passage only describes the risk treatment process or results without evidence of documentation or retention, or references documentation for non-AI risk treatments


## 8.4 — AI system impact assessment (operation)

*2 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `8.4/0` The organization shall perform AI system impact assessments according to 6.1.4 at planned intervals or when significant changes are proposed to occur.

- **subject** — AI system impact assessments - performed at planned intervals or when significant changes are proposed
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a repeatable process for conducting AI system impact assessments, specifying that assessments are done at scheduled intervals and/or when significant changes to the AI system are proposed, and referencing the criteria or method from 6.1.4
- **partial when** — the process is described for only one trigger (e.g., only at planned intervals or only for significant changes), or the process is stated but lacks reference to 6.1.4 criteria
- **unmet when** — a passage describes impact assessments for non-AI systems, or only states a responsibility to perform assessments without describing the process, or references an external process without showing its existence

### `8.4/1` The organization shall retain documented information of the results of all AI system impact assessments.

- **subject** — results of AI system impact assessments
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that documented information (records) of the results from every AI system impact assessment is retained and accessible
- **partial when** — records are retained for only some assessments, or retention is stated as an intention but not evidenced
- **unmet when** — a passage describes the process of performing assessments but does not mention retention of results, or references retention of results for non-AI system assessments, or only refers to retention of the assessment process rather than its results


## 9.1 — Monitoring, measurement, analysis and evaluation

*6 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `9.1/0` The organization shall determine what needs to be monitored and measured

- **subject** — items, processes, or aspects of the AI management system that require monitoring and measurement
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage identifies specific elements, processes, or outcomes within the AI management system that are to be monitored and measured
- **partial when** — only some relevant items or processes are identified, or the determination is stated as a future intention
- **unmet when** — no determination is made, or only a general statement about monitoring and measurement is provided without specifying what is to be monitored and measured

### `9.1/1` The organization shall determine the methods for monitoring, measurement, analysis and evaluation, as applicable, to ensure valid results

- **subject** — methods used for monitoring, measurement, analysis, and evaluation of the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage specifies the methods, tools, or techniques to be used for monitoring, measurement, analysis, and evaluation, and addresses how validity of results is ensured
- **partial when** — methods are identified for only some activities, or validity is not addressed for all methods
- **unmet when** — no methods are specified, or only a general statement about using methods is provided without details, or validity is not considered

### `9.1/2` The organization shall determine when the monitoring and measuring shall be performed

- **subject** — timing or frequency of monitoring and measuring activities for the AI management system
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage specifies the schedule, frequency, or triggers for monitoring and measuring activities
- **partial when** — timing is specified for only some activities, or only general intervals are given without specifics
- **unmet when** — no timing is specified, or only a general statement about monitoring and measuring is provided without reference to when

### `9.1/3` The organization shall determine when the results from monitoring and measurement shall be analysed and evaluated

- **subject** — timing or frequency of analysis and evaluation of monitoring and measurement results
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage specifies when the results will be analysed and evaluated, such as after each monitoring event, at regular intervals, or upon certain triggers
- **partial when** — timing is specified for only some results, or only general intervals are given without specifics
- **unmet when** — no timing is specified, or only a general statement about analysis and evaluation is provided without reference to when

### `9.1/4` Documented information shall be available as evidence of the results

- **subject** — results of monitoring, measurement, analysis, and evaluation activities
- **actor** — `organization` · **form** — `record`
- **met when** — a passage provides or references documented evidence (records, reports, logs) showing the results of monitoring, measurement, analysis, and evaluation
- **partial when** — records are available for only some activities or results, or evidence is incomplete
- **unmet when** — no documented evidence is available, or only a description of the process is provided without actual results

### `9.1/5` The organization shall evaluate the performance and the effectiveness of the AI management system

- **subject** — evaluation of performance and effectiveness of the AI management system
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a defined process or method for evaluating both the performance and effectiveness of the AI management system
- **partial when** — only performance or only effectiveness is addressed, or the process is described as an intention rather than an established practice
- **unmet when** — no process is described, or only a general statement about evaluation is provided without specifics, or only responsibilities are assigned without a process


## 9.2.1 — Internal audit - General

*3 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `9.2.1/0` Internal audits are conducted at planned intervals to provide information on whether the AI management system conforms to the organization’s own requirements for its AI management system.

- **subject** — internal audits of the AI management system against the organization’s own requirements
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that internal audits have been conducted, at planned intervals, specifically to assess conformity of the AI management system to the organization’s own requirements (audit reports, schedules, findings, or minutes referencing this criterion)
- **partial when** — audit activity is described but only some audits address the organization’s own requirements, or intervals are not planned but audits have occurred
- **unmet when** — audits are described but do not reference the organization’s own requirements, or only reference other standards or requirements; a plan to audit is stated but no evidence of actual audits

### `9.2.1/1` Internal audits are conducted at planned intervals to provide information on whether the AI management system conforms to the requirements of ISO/IEC 42001:2023.

- **subject** — internal audits of the AI management system against ISO/IEC 42001:2023 requirements
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that internal audits have been conducted, at planned intervals, specifically to assess conformity of the AI management system to the requirements of ISO/IEC 42001:2023 (audit reports, schedules, findings, or minutes referencing this criterion)
- **partial when** — audit activity is described but only some audits address ISO/IEC 42001:2023 requirements, or intervals are not planned but audits have occurred
- **unmet when** — audits are described but do not reference ISO/IEC 42001:2023 requirements, or only reference other standards or requirements; a plan to audit is stated but no evidence of actual audits

### `9.2.1/2` Internal audits are conducted at planned intervals to provide information on whether the AI management system is effectively implemented and maintained.

- **subject** — internal audits of the effective implementation and maintenance of the AI management system
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that internal audits have been conducted, at planned intervals, specifically to assess whether the AI management system is effectively implemented and maintained (audit reports, schedules, findings, or minutes referencing this criterion)
- **partial when** — audit activity is described but only some audits address effective implementation and maintenance, or intervals are not planned but audits have occurred
- **unmet when** — audits are described but do not reference effective implementation and maintenance, or only reference conformity; a plan to audit is stated but no evidence of actual audits


## 9.2.2 — Internal audit programme

*6 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `9.2.2/0` The organization shall plan, establish, implement and maintain (an) audit programme(s), including the frequency, methods, responsibilities, planning requirements and reporting.

- **subject** — internal audit programme(s) covering frequency, methods, responsibilities, planning requirements and reporting
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a repeatable process for internal audit programme(s) that includes how often audits occur, the methods used, who is responsible, how audits are planned, and how reporting is handled
- **partial when** — the process is described but omits one or more required elements (e.g., frequency is missing, or reporting is not addressed)
- **unmet when** — a passage describes an audit programme without addressing any of the required elements, or only references an intention to create a programme, or describes an audit process for a different management system

### `9.2.2/1` When establishing the internal audit programme(s), the organization shall consider the importance of the processes concerned and the results of previous audits.

- **subject** — consideration of process importance and previous audit results when establishing the internal audit programme(s)
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage states that the importance of the processes and the results of previous audits are considered when establishing the internal audit programme(s), and describes how this is done
- **partial when** — only one factor (either process importance or previous audit results) is considered, or the passage states an intention to consider but does not describe how
- **unmet when** — no mention of consideration of process importance or previous audit results, or consideration is described for a different programme

### `9.2.2/2` The organization shall define the audit objectives, criteria and scope for each audit.

- **subject** — audit objectives, criteria and scope for each audit
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage defines the objectives, criteria and scope for each internal audit
- **partial when** — only one or two of the three (objectives, criteria, scope) are defined, or definitions are incomplete
- **unmet when** — no definitions are provided, or definitions are for audits outside the AI management system

### `9.2.2/3` The organization shall select auditors and conduct audits to ensure objectivity and the impartiality of the audit process.

- **subject** — selection of auditors and conduct of audits ensuring objectivity and impartiality
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process for selecting auditors and conducting audits that ensures objectivity and impartiality (e.g., independence, avoidance of conflicts of interest)
- **partial when** — the process addresses only selection or only conduct, or objectivity/impartiality is mentioned but not ensured
- **unmet when** — auditor selection or audit conduct is described without reference to objectivity or impartiality, or the process is for a different management system

### `9.2.2/4` The organization shall ensure that the results of audits are reported to relevant managers.

- **subject** — reporting of audit results to relevant managers
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a process that ensures audit results are reported to relevant managers (e.g., defined recipients, reporting channels)
- **partial when** — the process describes reporting but does not specify relevant managers, or only some audit results are reported
- **unmet when** — audit results are not reported, or reporting is described for a different management system

### `9.2.2/5` Documented information shall be available as evidence of the implementation of the audit programme(s) and the audit results.

- **subject** — documented evidence of implementation of the audit programme(s) and audit results
- **actor** — `organization` · **form** — `record`
- **met when** — a passage provides or references documented information (records, reports, logs) showing the audit programme(s) were implemented and audit results exist
- **partial when** — documented information is available for either implementation or results, but not both, or only draft records are present
- **unmet when** — no documented information is available, or only a description of the process without records, or records are for a different management system


## 9.3.1 — Management review - General

*2 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `9.3.1/0` Top management shall review the organization’s AI management system at planned intervals

- **subject** — review of the AI management system - NOT any other management system
- **actor** — `top_management` · **form** — `record`
- **met when** — a passage evidences that top management has conducted a review of the AI management system, specifying that it occurred at planned intervals (e.g., meeting minutes, review schedule, signed review reports)
- **partial when** — a passage states an intention or plan to review, or describes a review process, but does not evidence that a review actually took place
- **unmet when** — a passage describes review of a different management system (e.g., quality, information security), or only assigns responsibility for review without evidence of occurrence, or references a review without providing evidence

### `9.3.1/1` Top management shall review the organization’s AI management system to ensure its continuing suitability, adequacy and effectiveness

- **subject** — review of the AI management system for suitability, adequacy and effectiveness
- **actor** — `top_management` · **form** — `record`
- **met when** — a passage evidences that the review by top management considered the AI management system’s suitability, adequacy and effectiveness (e.g., review agenda, minutes, report sections addressing these aspects)
- **partial when** — a passage evidences review but only addresses one or two of suitability, adequacy, or effectiveness, or states an intention to consider these without evidence of actual consideration
- **unmet when** — a passage describes review of the AI management system but does not address suitability, adequacy or effectiveness, or addresses these aspects for a different management system


## 9.3.2 — Management review inputs

*7 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `9.3.2/0` The management review includes the status of actions from previous management reviews

- **subject** — status of actions from previous management reviews
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the management review considered and documented the status (completion, progress, outstanding) of actions decided in prior management reviews
- **partial when** — only some previous actions are addressed, or the review notes intent to check status but does not document actual status
- **unmet when** — no mention of previous management review actions, or only a general statement about reviewing actions without specifics, or a cross-reference to an unseen artefact

### `9.3.2/1` The management review includes changes in external and internal issues that are relevant to the AI management system

- **subject** — changes in external and internal issues relevant to the AI management system
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the management review considered and documented changes in external (e.g., regulatory, technological) and internal (e.g., organizational, resource) issues affecting the AI management system
- **partial when** — only external or only internal issues are addressed, or changes are noted as a topic but not documented
- **unmet when** — no mention of changes in external or internal issues, or only a statement about monitoring issues without reference to changes, or a cross-reference to an unseen artefact

### `9.3.2/2` The management review includes changes in needs and expectations of interested parties that are relevant to the AI management system

- **subject** — changes in needs and expectations of interested parties relevant to the AI management system
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the management review considered and documented changes in the needs and expectations of interested parties (e.g., customers, regulators, employees) relevant to the AI management system
- **partial when** — only some interested parties are addressed, or changes are noted as a topic but not documented
- **unmet when** — no mention of changes in needs and expectations of interested parties, or only a statement about identifying interested parties without reference to changes, or a cross-reference to an unseen artefact

### `9.3.2/3` The management review includes information on the AI management system performance, including trends in nonconformities and corrective actions

- **subject** — trends in nonconformities and corrective actions related to the AI management system
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the management review considered and documented information on trends in nonconformities and corrective actions (e.g., frequency, types, resolution rates) for the AI management system
- **partial when** — only nonconformities or only corrective actions are addressed, or trends are noted as a topic but not documented
- **unmet when** — no mention of nonconformities or corrective actions, or only a statement about monitoring without reference to trends, or a cross-reference to an unseen artefact

### `9.3.2/4` The management review includes information on the AI management system performance, including trends in monitoring and measurement results

- **subject** — trends in monitoring and measurement results related to the AI management system
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the management review considered and documented information on trends in monitoring and measurement results (e.g., performance metrics, KPIs) for the AI management system
- **partial when** — only monitoring or only measurement results are addressed, or trends are noted as a topic but not documented
- **unmet when** — no mention of monitoring or measurement results, or only a statement about monitoring without reference to trends, or a cross-reference to an unseen artefact

### `9.3.2/5` The management review includes information on the AI management system performance, including trends in audit results

- **subject** — trends in audit results related to the AI management system
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the management review considered and documented information on trends in audit results (e.g., findings, compliance rates, recurring issues) for the AI management system
- **partial when** — audit results are noted as a topic but not documented, or only some audits are addressed
- **unmet when** — no mention of audit results, or only a statement about conducting audits without reference to trends, or a cross-reference to an unseen artefact

### `9.3.2/6` The management review includes opportunities for continual improvement

- **subject** — opportunities for continual improvement of the AI management system
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the management review considered and documented opportunities for continual improvement (e.g., suggestions, identified areas for enhancement) of the AI management system
- **partial when** — opportunities are noted as a topic but not documented, or only some improvement areas are addressed
- **unmet when** — no mention of continual improvement, or only a statement about the importance of improvement without reference to specific opportunities, or a cross-reference to an unseen artefact


## 9.3.3 — Management review results

*3 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `9.3.3/0` The results of the management review include decisions related to continual improvement opportunities

- **subject** — continual improvement opportunities identified in management review results
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage describes specific decisions made during management review regarding continual improvement opportunities for the AI management system
- **partial when** — the passage identifies improvement opportunities but does not record any decisions or actions taken
- **unmet when** — the passage only describes the management review process, or references improvement opportunities without linking them to decisions made in the review

### `9.3.3/1` The results of the management review include decisions related to any need for changes to the AI management system

- **subject** — need for changes to the AI management system identified in management review results
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage describes specific decisions made during management review regarding changes needed in the AI management system
- **partial when** — the passage identifies a need for change but does not record any decisions or actions taken
- **unmet when** — the passage only describes the management review process, or references changes without linking them to decisions made in the review

### `9.3.3/2` Documented information is available as evidence of the results of management reviews

- **subject** — results of management reviews
- **actor** — `organization` · **form** — `record`
- **met when** — a passage provides or references documented information (such as minutes, reports, or records) that evidences the results of management reviews
- **partial when** — a passage states that records exist but does not provide or reference them, or only partial results are documented
- **unmet when** — a passage describes the management review process but does not provide or reference any documented evidence of the results


## 10.1 — Continual improvement

*1 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `10.1/0` The organization shall continually improve the suitability, adequacy and effectiveness of the AI management system.

- **subject** — continual improvement of the AI management system's suitability, adequacy and effectiveness
- **actor** — `organization` · **form** — `process`
- **met when** — a passage describes a defined, repeatable process for ongoing evaluation and improvement of the AI management system, specifically addressing how suitability, adequacy, and effectiveness are assessed and enhanced over time
- **partial when** — a passage describes improvement activities for only one or two of suitability, adequacy, or effectiveness, or states an intention to improve without describing a process
- **unmet when** — a passage describes improvement of a different management system (e.g., quality, information security), or only assigns responsibility for improvement without describing a process, or references an unseen artefact


## 10.2 — Nonconformity and corrective action

*11 requirements · Annex A: **none** — the standard gives this clause no Annex A control and no Annex B guidance*

### `10.2/0` When a nonconformity occurs, the organization shall take action to control and correct it, as applicable.

- **subject** — actions taken to control and correct a nonconformity
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that specific actions were taken to control and correct a nonconformity after it occurred (e.g., containment, correction, mitigation steps)
- **partial when** — a passage describes an intention or plan to control/correct, but lacks evidence of actual action taken
- **unmet when** — a passage only describes the identification of a nonconformity, or only assigns responsibility, or only describes a procedure for correction without evidence of it being applied

### `10.2/1` When a nonconformity occurs, the organization shall deal with the consequences, as applicable.

- **subject** — actions taken to deal with the consequences of a nonconformity
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the organization addressed the consequences of a nonconformity (e.g., notification, remediation, compensation, impact mitigation)
- **partial when** — a passage describes an intention or plan to deal with consequences, but lacks evidence of actual action taken
- **unmet when** — a passage only describes the consequences without stating any action taken, or only describes a procedure for dealing with consequences without evidence of it being applied

### `10.2/2` The organization shall review the nonconformity to evaluate the need for action to eliminate its cause(s), so that it does not recur or occur elsewhere.

- **subject** — review of the nonconformity
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the nonconformity was reviewed to evaluate the need for action to eliminate its cause(s)
- **partial when** — a passage describes a review process but lacks evidence of it being applied to a specific nonconformity
- **unmet when** — a passage only describes the occurrence of a nonconformity, or only assigns responsibility for review, or only describes a procedure for review without evidence of it being applied

### `10.2/3` The organization shall determine the causes of the nonconformity to evaluate the need for action to eliminate its cause(s), so that it does not recur or occur elsewhere.

- **subject** — determination of the causes of a nonconformity
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the causes of a specific nonconformity were determined (e.g., root cause analysis, investigation results)
- **partial when** — a passage describes an intention or plan to determine causes, but lacks evidence of actual determination
- **unmet when** — a passage only describes the occurrence of a nonconformity, or only assigns responsibility for cause determination, or only describes a procedure for cause determination without evidence of it being applied

### `10.2/4` The organization shall determine if similar nonconformities exist or can potentially occur to evaluate the need for action to eliminate its cause(s), so that it does not recur or occur elsewhere.

- **subject** — determination of existence or potential occurrence of similar nonconformities
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the organization checked for similar nonconformities or potential occurrences (e.g., review of past incidents, risk assessment)
- **partial when** — a passage describes an intention or plan to check for similar nonconformities, but lacks evidence of actual determination
- **unmet when** — a passage only describes the occurrence of a nonconformity, or only assigns responsibility for checking, or only describes a procedure for checking without evidence of it being applied

### `10.2/5` The organization shall implement any action needed to eliminate the cause(s) of the nonconformity.

- **subject** — implementation of actions needed to eliminate the cause(s) of a nonconformity
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that corrective actions were implemented to eliminate the cause(s) of a nonconformity
- **partial when** — a passage describes an intention or plan to implement actions, but lacks evidence of actual implementation
- **unmet when** — a passage only describes the determination of actions needed, or only assigns responsibility for implementation, or only describes a procedure for implementation without evidence of it being applied

### `10.2/6` The organization shall review the effectiveness of any corrective action taken.

- **subject** — review of effectiveness of corrective actions
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that the effectiveness of corrective actions was reviewed (e.g., follow-up, monitoring, verification of resolution)
- **partial when** — a passage describes an intention or plan to review effectiveness, but lacks evidence of actual review
- **unmet when** — a passage only describes the implementation of corrective actions, or only assigns responsibility for review, or only describes a procedure for review without evidence of it being applied

### `10.2/7` The organization shall make changes to the AI management system, if necessary, following a nonconformity.

- **subject** — changes made to the AI management system as a result of a nonconformity
- **actor** — `organization` · **form** — `record`
- **met when** — a passage evidences that changes were made to the AI management system in response to a nonconformity (e.g., updates to procedures, controls, policies)
- **partial when** — a passage describes an intention or plan to make changes, but lacks evidence of actual change
- **unmet when** — a passage only describes the occurrence of a nonconformity, or only assigns responsibility for making changes, or only describes a procedure for making changes without evidence of it being applied

### `10.2/8` Corrective actions shall be appropriate to the effects of the nonconformities encountered.

- **subject** — appropriateness of corrective actions to the effects of nonconformities
- **actor** — `organization` · **form** — `determination`
- **met when** — a passage evidences that corrective actions were selected and justified as appropriate to the effects of the specific nonconformity (e.g., rationale, proportionality statement)
- **partial when** — a passage describes an intention or plan to select appropriate actions, but lacks evidence of actual determination or justification
- **unmet when** — a passage only describes the implementation of corrective actions without addressing appropriateness, or only assigns responsibility for selection, or only describes a procedure for selection without evidence of it being applied

### `10.2/9` Documented information shall be available as evidence of the nature of the nonconformities and any subsequent actions taken.

- **subject** — the nature of nonconformities and subsequent actions taken
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage provides or references documented information describing the nature of nonconformities and the actions taken in response
- **partial when** — documented information is available for some but not all nonconformities or actions taken
- **unmet when** — a passage only describes the occurrence of nonconformities or actions taken without providing or referencing documented information, or only describes a procedure for documentation without evidence of it being applied

### `10.2/10` Documented information shall be available as evidence of the results of any corrective action.

- **subject** — results of corrective actions
- **actor** — `organization` · **form** — `documented_information`
- **met when** — a passage provides or references documented information describing the results of corrective actions taken
- **partial when** — documented information is available for some but not all corrective actions
- **unmet when** — a passage only describes the implementation of corrective actions without providing or referencing documented information about their results, or only describes a procedure for documentation without evidence of it being applied

