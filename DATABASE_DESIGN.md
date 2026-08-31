# ISO 42001 Certification Tool — Database Design

## Status
Work-in-progress design notes, built up incrementally. This document currently covers only the **base registry** — organizations and users. Document storage, review comments, and gap analysis tables will be added in later sections once the registry is confirmed.

**Certification is at the organization level, not per-application/AI-system.** An earlier draft of this doc had an `applications` table (one AI system per org) sitting between organizations and documents; that's been dropped — a company certifies as a whole against a given standard, not one specific product it built. `documents` (and everything downstream) key off `organization_id` + `certification_standard` directly. See `frontend/app.js`'s data model comment for the confirmed shape.

---

## 1. Registry: Organizations, Users

### Purpose
Before any document, evidence, or audit finding can exist, the platform needs to know **whose** organization it belongs to. This section defines that foundation.

### Actors
Three actor concepts, backed by two tables:

| Actor | How it's represented |
|---|---|
| **Organization** | A row in `organizations`. No special "type" column — the same table holds client companies and audit firms alike. |
| **Developer** | A `users` row with `persona = 'developer'`. Belongs to the organization being certified. |
| **Internal Auditor** | A `users` row with `persona = 'auditor'` whose `organization_id` is the **same** as the organization being audited. |
| **External Auditor** | A `users` row with `persona = 'auditor'` whose `organization_id` is **different** from the organization being audited (i.e., belongs to a separate audit-firm organization). |

"Internal" vs "external" is **derived**, not stored — it falls out of comparing the acting auditor's `organization_id` to the organization whose documents they're viewing. No extra type flags or assignment tables were added, by design, to keep this layer simple.

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
  password_hash    VARCHAR(255) NOT NULL,  -- bcrypt hash; never decrypted, only re-hashed and compared at login
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Authentication is real (see `PHASE1_SCOPE.md`'s Authentication section): `POST /api/auth/register` / `POST /api/auth/login` issue a signed JWT that every write endpoint requires. There is intentionally no endpoint that lists all users — it would expose every email with no access control.

### Entity Relationships

```text
organizations (1) ──< (many) users
```

### Design notes
- One organization can have many users (confirmed cardinality).
- Auditor is a **role** (`persona`), not an organization type — the same `organizations` table serves both client companies and audit firms; what makes an auditor "internal" or "external" is purely which organization they happen to belong to relative to the organization being audited.
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
  certification_standard VARCHAR(20) NOT NULL,   -- 'iso9001' | 'iso42001' | 'iso27001'

  -- versioning
  document_group_id    UUID NOT NULL,             -- constant across all versions of "the same" document
  version_number        INT NOT NULL DEFAULT 1,
  is_current           BOOLEAN NOT NULL DEFAULT true,
  previous_version_id  UUID REFERENCES documents(id),

  -- descriptive metadata (fixed at creation, carried forward across versions)
  document_name        VARCHAR(500) NOT NULL,
  document_type        VARCHAR(100) NOT NULL,

  -- how this version was submitted: 'upload' | 'share_path' | 'zip'
  source_type           VARCHAR(20) NOT NULL,

  -- file — for 'share_path', storage_path holds the shared/network path itself
  -- and no bytes are ever transferred or stored server-side
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
CREATE INDEX idx_documents_active  ON documents(organization_id, certification_standard) WHERE is_current = true AND is_deleted = false;
```

### Operation semantics

- **Create**: developer inserts a row — `document_name`, `document_type`, `certification_standard`, `organization_id`, `submitted_by`, `submitted_at` are set once. `document_group_id` is a fresh UUID (this document's permanent identity across all future versions). `version_number = 1`, `is_current = true`.
- **Update** (a "document changes" event): the file is never overwritten in place. Instead:
  1. The existing current row is flipped to `is_current = false`.
  2. A **new row** is inserted with the same `document_group_id`, `version_number` incremented, `previous_version_id` pointing at the row it replaces, `is_current = true`.
  3. `document_name`, `document_type`, `certification_standard`, `organization_id`, `submitted_by`, `submitted_at` are carried forward unchanged from the original document — matching "everything remains the same."
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
- **Auditor visibility**: no separate access table needed yet — an auditor queries `documents WHERE organization_id = :target_org AND certification_standard = :standard AND is_current = true AND is_deleted = false`, scoped by the internal/external relationship defined in Section 1.
- **Review**: for each document, the auditor inserts one or more rows into `document_review_comments` referencing that `document_id`.
- **Developer visibility**: the developer sees comments by joining `document_review_comments` back to `documents` (via `document_id`) for documents they submitted.
- Comments reference a specific **version** (`document_id`, not `document_group_id`) — if a document is updated after a comment was made, the comment stays attached to the version it was actually written against.

---

## 4. Document Extraction (built)

### Purpose
Before the LLM clause-mapping pass (Section 5 below, still pending) can run, a document's raw bytes need to become text. This section is that conversion step — format-routed, run once per document version, and persisted rather than left as a transient value only used inside one LLM call.

### Schema

```sql
CREATE TABLE document_extractions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id       UUID NOT NULL UNIQUE REFERENCES documents(id),
  extraction_method VARCHAR(20) NOT NULL,  -- 'native' | 'ocr' | 'ocr_unavailable'
  extracted_text    TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE document_extracted_images (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_extraction_id  UUID NOT NULL REFERENCES document_extractions(id),
  page_number              INT,           -- NULL for docx/pptx (no page concept); set for PDF pages
  ocr_text                 TEXT,          -- NULL until OCR'd (or if OCR is unavailable)
  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

`document_id` is unique — one extraction row per document *version* (each new version, per Section 2's versioning semantics, gets re-extracted from scratch).

### Operation semantics
- **Format routing** (`app/extraction/document_extraction.py`): `.txt` is read directly; `.docx`/`.pptx` use local structured extraction (`python-docx`/`python-pptx`) with no cloud call; `.pdf` tries its native text layer first (PyMuPDF) and only falls back to OCR if every page's text layer is empty/near-empty (i.e. it's a scan, not born-digital).
- **OCR fallback** (`app/extraction/document_intelligence_client.py`): Azure AI Document Intelligence (Layout model), used only for scanned PDFs and for embedded images. If no Document Intelligence resource is configured, this is recorded honestly as `extraction_method = 'ocr_unavailable'` (empty text) rather than silently pretending extraction succeeded — the document upload itself still succeeds either way.
- **Embedded images** (`app/extraction/image_extractor.py`): pulled out separately from `.docx`/`.pptx` (their internal `word/media/`/`ppt/media/` zip entries) and from `.pdf` (PyMuPDF's per-page image xrefs), so a table-as-image inside an otherwise-native document still gets OCR'd rather than silently skipped.
- **Trigger**: `run_extraction()` (`app/tasks/extract_document.py`) runs synchronously, right after a document is stored (upload / share-path / zip / new version) — not yet via Celery, since no Redis broker is running locally. The same function is wrapped as a Celery task (`extract_document_task`) so switching to `.delay()` once Redis is available is a one-line change at the call site, not a rewrite. Extraction failure (unsupported format, unreachable share path, corrupt file) is caught and never blocks the document upload/version it's attached to.
- **Read access**: `GET /api/documents/{document_id}/extraction` returns the extraction (404 if none exists yet for that document version).

---

## 5. Gap Analysis — Findings (built)

### Purpose
Turns uploaded documents into reviewable, per-clause findings against all 70 requirements (38 Annex A controls + 32 clauses) of a standard. Mapping is fully automatic/content-based — a developer never tags a document with the clause(s) it's meant to satisfy — and analysis is **auditor-triggered**, not automatic on upload: a developer uploads a batch of evidence, then an auditor clicks **Analyze** to run the pass.

### Schema

```sql
CREATE TABLE findings (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id           UUID NOT NULL REFERENCES organizations(id),
  clause_id                 UUID NOT NULL REFERENCES clauses(id),
  certification_standard    VARCHAR(20) NOT NULL,

  status                    VARCHAR(20) NOT NULL DEFAULT 'not_assessed',
    -- 'not_assessed' | 'met' | 'partial' | 'gap' | 'not_applicable'

  evidence_document_id      UUID REFERENCES documents(id),   -- primary/highest-scoring contributor
  evidence_document_ids     UUID[],                          -- every contributing document, for combined findings

  relevance_score           DECIMAL(5,2),
  coverage_score            DECIMAL(5,2),
  rationale                 TEXT,
  mapping_method            VARCHAR(20) NOT NULL DEFAULT 'auto',  -- 'auto' | 'confirmed' | 'manual'

  previous_relevance_score  DECIMAL(5,2),   -- preserved on override
  previous_coverage_score   DECIMAL(5,2),

  reviewed_by               UUID REFERENCES users(id),
  reviewed_at                TIMESTAMPTZ,

  created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(organization_id, clause_id)
);
```

`evidence_document_ids` (a plain array column, same pattern as `clauses.evidence_requirements`) is the only schema addition beyond what the initial migration already created — no new tables. A clause with no `findings` row at all simply reads as `not_assessed`; there's no need for a placeholder row.

### Pipeline (`POST /organizations/{id}/standards/{standard}/analyze`, auditor-only)

1. **Map (per document, one LLM call each, no caching):** every currently-active document (`is_current=true`, `is_deleted=false`) is sent to the LLM once, against the *full* 70-requirement list for its standard (`app/ai/clause_mapper.py`, wrapping `app/ai/openai_client.py`'s `get_control_mappings`). No developer tagging exists to narrow this — the LLM decides relevance from content alone, and is instructed to omit anything it isn't confident about.
2. **Reduce/combine (per clause, full recompute):** results are grouped by requirement code (`app/tasks/run_gap_analysis.py`), then for every clause in the standard (`app/ai/aggregator.py`):
   - 0 contributing documents → the finding (if any, and if not already `confirmed`/`manual`) is deleted, dropping back to `not_assessed`.
   - 1 contributing document → written straight into the finding.
   - 2+ contributing documents → one additional LLM call (`prompt_library/reduce_prompt.py`) merges every contributor's quoted excerpt into a single combined `coverage_score`/`relevance_score`/`rationale` (evidence for one control is often split across documents — e.g. a policy's "development" and "use" sections in separate files — and this is what lets them jointly satisfy it).
3. A finding already `mapping_method IN ('confirmed', 'manual')` is **never** touched by steps 1-2 — an auditor's decision survives every later re-run.
4. **Status derivation:** `coverage_score >= 70` → `met`; `30-69` → `partial`; `< 30` → `gap`.

Every "Analyze" click is a full, stateless recompute from the current document set — this is also what correctly drops a finding's evidence when its backing document is later soft-deleted.

### Review
`PATCH /findings/{id}` — auditor-only (`403` for a developer, same check as `document_review_comments`): `action: "confirm"` sets `mapping_method='confirmed'`; `action: "override"` moves the current scores into `previous_*_score` and sets `mapping_method='manual'`.

### Read access
- `GET /organizations/{id}/standards/{standard}/findings` — all 70 requirements, LEFT JOINed against this organization's finding for each.
- `GET /organizations/{id}/standards/{standard}/report` — the same list plus summary counts (met/partial/gap/not_assessed), both overall and for Annex A controls alone.
