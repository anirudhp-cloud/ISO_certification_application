# ISO 42001 Certification Platform — PRD & Database Design

## Note on this document
This file merges the original platform PRD with the detailed database design worked out afterward, scoped down to **ISO/IEC 42001 only**, using **GPT** as the LLM, and **without RBAC** (deferred). The database design in Part 2 is more detailed and more current than the placeholder entity list in Part 1, Section 6 ("Database Model") — treat Part 2 as authoritative for schema, and Part 1 as the product/architecture framing around it.

---

# Part 1 — Product Requirements Document

## Purpose
This document describes an enterprise SaaS platform that combines:
- ISO compliance automation
- AI-powered document processing
- RAG-based retrieval
- An agentic auditor copilot
- Reporting and audit management

## 1. Executive Summary
The platform automates document collection, parsing, evidence extraction, clause mapping, compliance evaluation, findings generation, human review, and reporting.

## 2. Product Vision
Build a multi-standard compliance platform that reduces audit preparation time while keeping auditors in the approval loop.

## 3. Core Modules

### Compliance Automation Engine
- Document ingestion
- OCR and parsing
- Metadata extraction
- Clause mapping
- Evidence extraction
- Rule validation
- LLM evaluation
- Findings generation
- Report generation

### Auditor Copilot
- Explain documents
- Search evidence
- Compare versions
- Edit policies and SOPs
- Generate corrective actions

## 4. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript |
| Backend | FastAPI |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Queue | Redis + Celery |
| Storage | Azure Blob Storage |
| OCR | Azure Document Intelligence |
| LLM | GPT |
| Deployment | Docker + Azure Container Apps |

## 5. High-Level Architecture

```text
React
  |
FastAPI
  |
+-- PostgreSQL
+-- Redis
+-- Blob Storage
+-- GPT
```

## 6. Database Model

> Superseded by Part 2 below. Original entity list, kept for reference:
> organizations, departments, users, audits, standards, clauses, controls, documents, document_metadata, document_chunks, evidence, findings, corrective_actions, chat_sessions, chat_messages

## 7. API Endpoints

- POST /api/auth/login
- POST /api/documents/upload
- GET /api/documents
- POST /api/audits
- GET /api/findings
- POST /api/chat
- GET /api/reports

## 8. Security
- RBAC *(deferred — see Part 2, Section 1 design notes)*
- JWT
- Audit logs
- Encryption at rest
- Encryption in transit

## 9. Roadmap
- ISO/IEC 42001
- Continuous compliance

---

# Part 2 — Database Design

## Status
Work-in-progress design notes, built up incrementally. This document currently covers the **base registry** (organizations, users, applications), **document storage**, and **review comments**. Gap analysis is not yet finalized.

---

## 1. Registry: Organizations, Users, Applications

### Purpose
Before any document, evidence, or audit finding can exist, the platform needs to know **whose** organization it belongs to and **which application** (AI system) it concerns. This section defines that foundation.

### Actors
Four actor concepts, backed by two tables:

| Actor | How it's represented |
|---|---|
| **Organization** | A row in `organizations`. No special "type" column — the same table holds client companies and audit firms alike. |
| **Developer** | A `users` row with `persona = 'developer'`. Belongs to the organization that owns the application. |
| **Internal Auditor** | A `users` row with `persona = 'auditor'` whose `organization_id` is the **same** as the application's `organization_id`. |
| **External Auditor** | A `users` row with `persona = 'auditor'` whose `organization_id` is **different** from the application's `organization_id` (i.e., belongs to a separate audit-firm organization). |

"Internal" vs "external" is **derived**, not stored — it falls out of comparing `users.organization_id` to `applications.organization_id`. No extra type flags or assignment tables were added, by design, to keep this layer simple.

### Schema

```sql
CREATE TABLE organizations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        VARCHAR(255) NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  UUID NOT NULL REFERENCES organizations(id),
  name             VARCHAR(255) NOT NULL,
  email            VARCHAR(255) NOT NULL UNIQUE,
  persona          VARCHAR(20) NOT NULL CHECK (persona IN ('developer', 'auditor')),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE applications (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  UUID NOT NULL REFERENCES organizations(id),
  name             VARCHAR(255) NOT NULL,
  registered_by    UUID NOT NULL REFERENCES users(id),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Entity Relationships

```text
organizations (1) ──< (many) users
organizations (1) ──< (many) applications
users (1) ──< (many) applications   [via registered_by]
```

### Design notes
- One organization can have many users and many applications (confirmed cardinality).
- Auditor is a **role** (`persona`), not an organization type — the same `organizations` table serves both client companies and audit firms; what makes an auditor "internal" or "external" is purely which organization they happen to belong to relative to the application in question.
- RBAC (fine-grained permissions, role-permission matrices) is explicitly **out of scope for now** — `persona` here only distinguishes developer vs auditor at the identity level, not what either is allowed to do.
- Deferred for a later section: how documents/review comments/gap analysis route between a developer and an auditor, and between two auditors in the same organization for peer review — this needs the registry settled first.

---

## 2. Document Storage

### Purpose
Developers upload evidence documents against an application; auditors (internal or external, per Section 1) review them and leave comments back. Documents must be **versioned on update** and **soft-deleted** — nothing is ever physically lost, since ISO audits need a defensible trail of what existed, when it changed, and who touched it.

### Schema

```sql
CREATE TABLE documents (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id      UUID NOT NULL REFERENCES organizations(id),
  application_id       UUID NOT NULL REFERENCES applications(id),

  -- versioning
  document_group_id    UUID NOT NULL,             -- constant across all versions of "the same" document
  version_number        INT NOT NULL DEFAULT 1,
  is_current           BOOLEAN NOT NULL DEFAULT true,
  previous_version_id  UUID REFERENCES documents(id),

  -- descriptive metadata (fixed at creation, carried forward across versions)
  document_name        VARCHAR(500) NOT NULL,
  document_type        VARCHAR(100) NOT NULL,

  -- file
  file_name             VARCHAR(500) NOT NULL,
  storage_path          VARCHAR(1000) NOT NULL,

  -- who created the document (the original submission — stays the same across versions)
  submitted_by          UUID NOT NULL REFERENCES users(id),
  submitted_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- who produced *this* version, and when
  updated_by            UUID REFERENCES users(id),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- soft delete
  is_deleted            BOOLEAN NOT NULL DEFAULT false,
  deleted_by            UUID REFERENCES users(id),
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_documents_group   ON documents(document_group_id);
CREATE INDEX idx_documents_active  ON documents(application_id) WHERE is_current = true AND is_deleted = false;
```

### Operation semantics

- **Create**: developer inserts a row — `document_name`, `document_type`, `application_id`, `organization_id`, `submitted_by`, `submitted_at` are set once. `document_group_id` is a fresh UUID (this document's permanent identity across all future versions). `version_number = 1`, `is_current = true`.
- **Update** (a "document changes" event): the file is never overwritten in place. Instead:
  1. The existing current row is flipped to `is_current = false`.
  2. A **new row** is inserted with the same `document_group_id`, `version_number` incremented, `previous_version_id` pointing at the row it replaces, `is_current = true`.
  3. `document_name`, `document_type`, `application_id`, `organization_id`, `submitted_by`, `submitted_at` are carried forward unchanged from the original document — matching "everything remains the same."
  4. `updated_by` / `updated_at` are set fresh on the new row — who made this update, and when.
- **Delete**: a soft delete — search for the document by `document_group_id`, then set `is_deleted = true`, `deleted_by`, `deleted_at` on all rows in that group (every version). Rows stay in the table permanently; they just drop out of the active view (`WHERE is_deleted = false`).

---

## 3. Review Comments

### Purpose
Every document uploaded by a developer becomes visible to the auditor(s) engaged on that application. An auditor reviews a document and leaves comments back against it, for the developer to see and act on.

### Schema

```sql
CREATE TABLE document_review_comments (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id   UUID NOT NULL REFERENCES documents(id),
  reviewed_by   UUID NOT NULL REFERENCES users(id),   -- the auditor who wrote the comment
  comment_text  TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_review_comments_document ON document_review_comments(document_id);
```

### Operation semantics
- **Auditor visibility**: no separate access table needed yet — an auditor queries `documents WHERE application_id = :their_application AND is_current = true AND is_deleted = false`, scoped by the internal/external relationship defined in Section 1.
- **Review**: for each document, the auditor inserts one or more rows into `document_review_comments` referencing that `document_id`.
- **Developer visibility**: the developer sees comments by joining `document_review_comments` back to `documents` (via `document_id`) for documents they submitted.
- Comments reference a specific **version** (`document_id`, not `document_group_id`) — if a document is updated after a comment was made, the comment stays attached to the version it was actually written against.

---

## 4. Gap Analysis — Requirement Mapping

### Purpose
Every submitted document needs to be linked to the requirements it provides evidence for — both the ISO/IEC 42001 Annex A **controls** and the clause 4-10 **clauses** it's evidencing. Doing this by hand alone doesn't scale (dozens of documents × 38+ requirements); doing it fully automatically is unsafe for a certification context (an unreviewed LLM mapping must never silently become an audit finding). The design is **LLM-suggests, auditor-confirms**: every mapping starts as a machine-generated suggestion and only counts once a human has looked at it.

This platform is scoped to ISO/IEC 42001 only (see the note at the top of this document), but the schema below is written to also hold ISO 27001 and ISO 9001 requirements without a redesign, because the mapping mechanics (score, rationale, auto/confirm/override) are identical regardless of standard or requirement type — see **Framework isolation** below for the rule that keeps this from leaking across standards.

### Schema

```sql
CREATE TABLE frameworks (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(20) NOT NULL UNIQUE      -- 'ISO42001' | 'ISO27001' | 'ISO9001'
);

CREATE TABLE requirements (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  framework_id          UUID NOT NULL REFERENCES frameworks(id),
  requirement_type      VARCHAR(20) NOT NULL,           -- 'clause' | 'control'
  code                  VARCHAR(20)  NOT NULL,          -- e.g. 'A.6.2.2' or '6.1.2'
  category              VARCHAR(255),                   -- Annex A theme, or clause group
  title                 VARCHAR(500) NOT NULL,
  description           TEXT,
  evidence_requirements TEXT[],                         -- may be empty for ISO 9001 clauses
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(framework_id, code)
);
CREATE INDEX idx_requirements_framework ON requirements(framework_id);
```
Seeded once per standard (ISO 42001's 38 Annex A controls + its clauses now; ISO 27001's 93 controls + clauses, and ISO 9001's clauses, when those standards come into scope) — not user-editable through the app.

```sql
CREATE TABLE document_requirement_mappings (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id               UUID NOT NULL REFERENCES documents(id),
  requirement_id             UUID NOT NULL REFERENCES requirements(id),

  relevance_score            DECIMAL(5,2),                        -- 0-100
  coverage_score              DECIMAL(5,2),                        -- 0-100
  mapping_method             VARCHAR(20) NOT NULL DEFAULT 'auto',  -- auto | confirmed | manual

  llm_rationale               TEXT,                                -- quoted passage + reasoning
  previous_relevance_score    DECIMAL(5,2),                        -- preserved on override
  previous_coverage_score     DECIMAL(5,2),

  reviewed_by                 UUID REFERENCES users(id),
  reviewed_at                 TIMESTAMPTZ,

  created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(document_id, requirement_id)
);

CREATE INDEX idx_drm_document    ON document_requirement_mappings(document_id);
CREATE INDEX idx_drm_requirement ON document_requirement_mappings(requirement_id);
```

### Framework isolation — no cross-standard leakage
Each application/assessment is opened against exactly the framework(s) the organization is being audited for. Even though ISO 42001, 27001, and 9001 share near-identical clause structure (all built on the ISO Annex SL "High Level Structure"), **that similarity is never used to auto-suggest or carry evidence across standards**:
- The requirement-mapping LLM call for a given document is only ever given the `requirements` rows belonging to the framework(s) that document's application is actually being assessed against. Rows for other frameworks are not loaded into the prompt, not suggested, not shown.
- An organization approaching this platform for ISO 42001 only interacts with ISO 42001 requirements — full stop, regardless of how similar another standard's clause text is.
- The `requirements`/`document_requirement_mappings` tables are shared **purely as schema/engineering convenience** (one migration, one confirm/override pipeline, one review queue implementation to maintain) — not as a shared evidence pool. If an organization later opens a separate assessment for a second standard, that is a distinct assessment with its own scope; nothing carries over automatically, even for a document re-uploaded unchanged.

### Operation semantics
1. **Document uploaded/versioned** → an async job is enqueued against the new `document_id`, scoped to the framework(s) of its application's assessment.
2. **Auto-mapping job**: extracts document text (existing OCR/parsing pipeline), sends it plus only the in-scope framework's requirement list to the LLM in one call (38 requirements for ISO 42001 alone comfortably fits in a single prompt — no retrieval/embedding step needed at this scale), and receives a shortlist of applicable requirements with scores and a rationale that quotes the source text. Rows are inserted with `mapping_method = 'auto'`, `reviewed_by = NULL`.
3. **Auditor review queue**: shows every `auto` row for documents in the auditor's scope, with the requirement text, the LLM's score, and its quoted rationale next to the source document.
4. **Confirm** → `mapping_method → 'confirmed'`, `reviewed_by`/`reviewed_at` set, scores unchanged.
5. **Override** → auditor edits `relevance_score`/`coverage_score`; the prior values move into `previous_relevance_score`/`previous_coverage_score` (never deleted), `mapping_method → 'manual'`, `reviewed_by`/`reviewed_at` set.
6. **Downstream consumers** (findings, reports, dashboards) only read rows where `mapping_method IN ('confirmed', 'manual')` — a raw `auto` row never counts as evidence of compliance until a human has acted on it, and rollups are always computed per-framework, never blended across standards.
