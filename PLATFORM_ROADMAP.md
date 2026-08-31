# ISO Certification Platform — Combined Roadmap: Phase 1 + Phase 2

## Status
Combined scope document merging `PHASE1_SCOPE.md` (Compliance Engine) and `PHASE2_SCOPE.md` (Auditor Copilot / RAG). Builds on the registry design in `ISO42001_Certification_Platform.md` (Part 2) and the ingestion/extraction/cost discussion worked out in conversation.

---

# Phase 1 — Compliance Engine (no RAG)

## Objective
Take a document a developer uploads, work out which clauses of the selected standard it satisfies, surface the gaps, and let an auditor turn that into a reviewed, defensible finding — without any open-ended chat or cross-document retrieval.

## In scope

### 1. Registry & standard selection
- Organizations, users (developer/auditor persona, no RBAC/auth yet), applications — as already prototyped in `frontend/`.
- Certification-standard selection (ISO 9001 / ISO/IEC 42001 / ISO/IEC 27001), one per application, scoping the dashboard.

### 2. Document ingestion
- Three ingestion methods: manual upload, share-path reference, zip upload (extract → one document per file).
- Versioning + soft delete, as defined in the existing `documents` schema.

### 3. Format routing & extraction
- `.txt` → read directly.
- `.docx` / `.pptx` / `.xlsx` → local structured extraction (no cloud call) — `python-docx`, `python-pptx`, `openpyxl`/`pandas`.
- `.pdf` → native text-layer extraction first; Azure Document Intelligence (Layout model) only as OCR fallback for scanned/image pages.
- **Embedded-image sub-step**: any format can contain a picture of a table or text-bearing image (a pasted screenshot, a scanned form dropped into a docx/pptx/xlsx). These are extracted as separate image objects and OCR'd individually — extraction is element-level, not just file-level.
- Result persisted as a new `document_extractions` row per document version (never left as a transient value only used inside one LLM call).

### 4. Standards & clause catalog (new)
- `standards` (ISO 9001 / 42001 / 27001) and `clauses`/`controls` tables — the fixed reference data the LLM pass evaluates documents against.

### 5. Clause-mapping / gap analysis (LLM pass)
- GPT-4.1 mini, batched per document (or per major section) against the relevant clause subset — not one call per clause, and not one call per document per clause.
- Structured JSON output: `clause_id`, `status` (met / partial / gap / not_applicable), `evidence_quote`, `location`, `confidence`.
- At small document sets, a single holistic call across an application's documents can fit GPT-4.1 mini's ~1M-token context window. At this platform's actual scale (40 documents × 40 pages/application ≈ 1.04M tokens), that no longer fits — so the pass is **per-document calls (map) + a small cross-document aggregation call (reduce)**, not one mega-call.

### 6. Findings & human review
- `findings` table: one row per (application, clause), holding current status, evidence reference, and a link back to the document version it came from.
- Findings land as drafts; an auditor accepts/overrides/annotates each one. Only accepted findings count toward readiness.
- Aggregated per-application readiness score (e.g. "22 met / 9 partial / 7 gap out of 38 clauses").

### 7. Reporting
- Export a per-application, per-standard compliance readiness report (clause-by-clause status + evidence citations + open gaps).

## New data introduced in Phase 1 (schema detail pending)
- `standards`, `clauses`
- `document_extractions`
- `findings`

## API surface (Phase 1)
- `POST /api/applications/{id}/documents` (upload / share-path / zip variants)
- `GET /api/applications/{id}/documents`
- `POST /api/documents/{id}/comments`, `GET /api/documents/{id}/comments`
- `POST /api/applications/{id}/analyze` — triggers the clause-mapping pass
- `GET /api/applications/{id}/findings`
- `PATCH /api/findings/{id}` — auditor accept/override
- `GET /api/applications/{id}/report`

## UI surface (Phase 1)
- Existing mockup screens (user switch, standard select, dashboard, application detail, document upload tabs, version history, comments).
- New: Findings review screen (per-application clause list with status, evidence, accept/override controls) and a report view/export.

## Explicitly out of scope for Phase 1
- Embeddings, vector search, RAG.
- Auditor copilot chat, cross-document semantic search, version-diff assistant.
- Continuous monitoring, OCR/vision compliance scanning (deepfake/PII-in-image), sector packs, SharePoint/Jira integration — see Phase 2 and beyond.
- RBAC/authentication (still deferred, per earlier decision).

## Exit criteria
A developer can upload documents for an application, an LLM pass produces draft clause findings, an auditor reviews/accepts them, and a readiness report can be generated — end to end, without any conversational or retrieval component.

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript | Per product decision; served as a static SPA |
| Backend API | FastAPI (Python) | Async-friendly, same language as the extraction/LLM code |
| Background jobs | Celery + Redis | OCR calls, LLM calls, and zip extraction are all slow enough to need a queue, not an inline request/response call |
| Database | PostgreSQL | Registry, documents, findings — relational, transactional |
| File storage | Azure Blob Storage | Original files, behind the `StorageBackend` interface already scaffolded |
| OCR / structure | Azure AI Document Intelligence (Layout model) | Scanned-page and embedded-image fallback only — native parsing is the default path |
| Local text extraction | `python-docx`, `python-pptx`, `openpyxl`/`pandas`, stdlib file read | Free, instant, lossless for born-digital content |
| LLM | Azure OpenAI — GPT-4.1 mini | Clause mapping, gap analysis, structured JSON findings |
| Deployment | Docker containers on Azure Container Apps | Consumption plan — scales to zero between analysis runs, which matters since load is bursty (uploads/analysis), not constant |

## Architecture

```text
React SPA (Azure Static Web Apps)
        |
        v
FastAPI (Azure Container Apps)  ---->  PostgreSQL (registry, documents, findings)
        |                       ---->  Azure Blob Storage (original files)
        |
        v
Celery worker (Azure Container Apps)
        |
        +--> Format router
        |      .txt / .docx / .pptx / .xlsx  -> local parser (free)
        |      .pdf (native text layer)       -> local parser (free)
        |      scanned page / embedded image  -> Azure AI Document Intelligence (Layout)
        |
        +--> document_extractions (persisted text/structure, per document version)
        |
        +--> GPT-4.1 mini: per-document clause mapping (map)
        |
        +--> GPT-4.1 mini: cross-document aggregation (reduce)
        |
        v
findings table  -->  auditor review UI  -->  readiness report
```

Redis sits behind Celery as the task queue/broker — not used for anything else in Phase 1.

## Cost Estimate

Two separate cost centers: **cloud infrastructure** (fixed-ish, scales with load) and **AI model/OCR usage** (scales with document volume). Figures below are sized for a starting deployment; treat them as a planning baseline, not a quote — check the Azure pricing calculator for your actual region/commitment before budgeting.

### Cloud infrastructure (monthly, sourced from current Azure pricing)

| Component | Sizing assumption | Est. cost/month |
|---|---|---|
| Azure Static Web Apps (frontend) | Free tier (100GB bandwidth) | $0 (Standard tier if you need staging slots/SLA: ~$9) |
| Azure Container Apps — API | Consumption plan, ~0.5 vCPU / 1 GiB average, scale-to-zero when idle | ~$40-60 |
| Azure Container Apps — Celery worker | Same consumption plan, bursts during upload/analysis | ~$40-60 |
| Azure Cache for Redis | Basic C0 (250MB) — task queue only | ~$16 |
| Azure Database for PostgreSQL Flexible Server | Burstable B2s (2 vCore/4GiB) | ~$50 (+ storage, billed separately, typically well under $10/month at this data volume) |
| Azure Blob Storage (Hot tier) | ~$0.018-0.023/GB/month; at 100 applications × 40 docs × ~10MB avg ≈ 40GB | ~$1 |
| **Subtotal — infrastructure** | | **~$150-190/month** |

This scales in steps, not linearly — e.g. Postgres and Container Apps tiers stay flat until you outgrow them, then jump to the next tier.

### AI model / OCR usage (scales with document volume)

Sized for this platform's actual document profile: 40 documents/application, each ≥40 pages, mixing text/images/native tables/tables-as-images.

| Scenario | Est. cost/application | At 100 applications | At 500 applications |
|---|---|---|---|
| Best case (mostly native docs, few embedded images) | ~$4.75 | ~$475 | ~$2,375 |
| Baseline (40% scanned, 10 embedded images/doc) | ~$11.15 | ~$1,115 | ~$5,575 |
| Worst case (mostly scans, image-heavy) | ~$20-37 | ~$2,000-3,700 | ~$10,000-18,500 |

Document Intelligence OCR (whole-page + embedded-image) dominates this line, not GPT-4.1 mini — minimizing unnecessary OCR calls (native-extraction-first, OCR only for true scans/images) is the highest-leverage cost control here.

### Phase 1 monthly total (baseline scenario, 100 applications)

**~$150-190 (infrastructure) + ~$1,115 (AI/OCR) ≈ $1,265-1,305/month**

---

# Phase 2 — Auditor Copilot (RAG)

## Objective
Let a developer or auditor ask open-ended questions across a growing, multi-document corpus ("explain this document," "find every mention of data retention," "compare v1 vs v2") — the class of request that doesn't fit the fixed clause-catalog pass from Phase 1 and needs retrieval instead of exhaustive processing.

## Dependency
Requires `document_extractions` (Phase 1) as the source text to chunk and embed. Nothing here re-extracts documents — it consumes what Phase 1 already persisted.

## In scope

### 1. Chunking & embeddings
- Semantic/section-aware chunking of each `document_extractions` row (~500-1000 tokens/chunk), independent of Phase 1's map-merge chunking (different purpose: retrieval unit, not context-window-fitting).
- Embedding each chunk (e.g. `text-embedding-3-small`).

### 2. Retrieval layer — open decision
- **Option A: pgvector** — chunks + embeddings live in the existing Postgres instance. No new service, no extra fixed cost, single transactional store.
- **Option B: Azure AI Search** — managed indexing/hybrid search/security trimming, but a separate billed service (~$74+/month fixed) and a second data store to keep in sync.
- Recommendation: start with pgvector given current scale; revisit Azure AI Search only if hybrid-ranking, AAD security trimming, or multi-modal indexing become real requirements.

### 3. Copilot chat
- RAG loop: embed the question → similarity search over `document_chunks` → inject top-k matches into the GPT-4.1 mini prompt → answer with citations back to document/page.
- Scoped per application/organization (never retrieves across tenants).

### 4. Cross-document search
- "Find evidence of X across all documents for this application" — same retrieval layer, presented as search rather than chat.

### 5. Version comparison assistant
- Given two versions of the same `document_group_id`, retrieve both, ask the LLM to summarize material differences.

### 6. Corrective-action drafting
- For an accepted `gap` finding, the copilot drafts a suggested corrective action using the retrieved context — still lands as a draft an auditor must accept, same human-in-the-loop rule as Phase 1.

## New data introduced
- `document_chunks` (chunk text, page/section ref, token count, embedding vector, FK to `document_extractions`)
- `chat_sessions`, `chat_messages` (per the original PRD entity list)

## API surface (Phase 2)
- `POST /api/chat` (session-scoped copilot turn)
- `GET /api/applications/{id}/search?q=...`
- `POST /api/documents/{group_id}/compare-versions`
- `POST /api/findings/{id}/draft-corrective-action`

## UI surface (Phase 2)
- Copilot chat panel (application-scoped).
- Search bar over documents/evidence.
- Version-compare view (diff-style summary).
- "Draft corrective action" button on a gap finding, feeding into the existing comments/review flow.

## Explicitly out of scope for Phase 2 (later roadmap, unscheduled)
- Continuous monitoring of deployed AI systems (webhook-based drift/quality detection).
- OCR/vision compliance scanning (deepfake detection, C2PA/EXIF provenance, PII-in-image).
- AI system inventory / shadow AI discovery.
- Sector packs (Healthcare/BFSI/Government), SharePoint/Jira integration.
- RBAC/authentication (still deferred).

## Exit criteria
A user can ask the copilot a free-form question about an application's documents and get a grounded, cited answer pulled from actual uploaded evidence — without the answer requiring a full re-run of the Phase 1 clause-mapping pass.

## Tech Stack

Everything from Phase 1, plus:

| Layer | Choice | Why |
|---|---|---|
| Vector storage | pgvector extension on the existing PostgreSQL instance | No new service, no second data store to keep in sync, negligible extra cost at this scale (see below) |
| Embeddings | Azure OpenAI `text-embedding-3-small` | Cheap, sufficient quality for compliance-document retrieval |
| Retrieval | Custom RAG loop in FastAPI (embed query -> pgvector similarity search -> inject into prompt) | Keeps retrieval logic and access-control (org/application scoping) in the same codebase as everything else |
| Chat/session state | New `chat_sessions` / `chat_messages` tables in the same Postgres instance | Consistent with everything else being one relational store |

**Open alternative, not chosen by default:** Azure AI Search could replace the pgvector + custom-retrieval-loop combination with a managed indexing/hybrid-search/security-trimming service. It's a legitimate option if you later need enterprise-scale hybrid ranking or AAD-based security trimming — see the Cost Estimate below for why it's not the default pick right now.

## Architecture

```text
React SPA
   |
   v
FastAPI  --(question)-->  Embed query (Azure OpenAI embeddings)
   |                              |
   |                              v
   |                    pgvector similarity search
   |                    (scoped to org_id / application_id)
   |                              |
   |                              v
   |                    Top-k document_chunks
   |                              |
   v                              v
   +-------> Prompt assembly (question + retrieved chunks) -------> GPT-4.1 mini
                                                                        |
                                                                        v
                                                          Grounded answer + citations
                                                          (document, page/section)
```

`document_chunks` (chunk text, page/section ref, embedding vector) is populated once per document version by chunking `document_extractions` from Phase 1 — no re-extraction happens here.

## Cost Estimate

### Cloud infrastructure — incremental over Phase 1

| Component | Sizing assumption | Est. cost/month |
|---|---|---|
| pgvector (same Postgres instance) | Embeddings for ~1,600 pages × 40 docs/app in ~1,000-token chunks ≈ ~6MB/application of vector data | Negligible — likely no tier change needed until very large scale |
| **If Azure AI Search chosen instead of pgvector** | Basic tier | ~$74/month flat (Standard S1 ~$245-250/month if you outgrow Basic's 15GB/15-index limit) |

Azure AI Search's cost is a **step function tied to storage/index count, not document count** — at 100 applications × 40 docs, you're unlikely to need more than Basic tier on raw storage, but it's still a fixed monthly commitment pgvector doesn't add.

### AI model usage — incremental over Phase 1

| Item | Calculation | Est. cost |
|---|---|---|
| Embeddings (one-time per document version) | ~1.04M tokens/application × $0.02/1M | ~$0.02/application |
| Copilot chat turns | ~2-4k tokens/turn (question + retrieved chunks + history) × $0.40/1M in + $1.60/1M out | ~$0.002-0.005/turn |

At 100 applications and, say, 500 chat turns/month total: embeddings ≈ $2, chat ≈ $1-2.50. **This entire layer adds well under $10/month in model cost** at this scale — it's the smallest line item in the whole system.

### Phase 2 incremental monthly total (100 applications, pgvector chosen)

**~$0 additional infrastructure (same Postgres) + ~$5-10 additional AI usage ≈ under $15/month on top of Phase 1's total.**

If Azure AI Search is chosen instead of pgvector, add its flat ~$74-250/month regardless of usage.

---

# Combined Total (Phase 1 + Phase 2, baseline scenario, 100 applications)

| | Infrastructure | AI/OCR usage | Total |
|---|---|---|---|
| Phase 1 | ~$150-190/month | ~$1,115/month | ~$1,265-1,305/month |
| Phase 2 (pgvector) | ~$0 additional | ~$5-10/month additional | ~$5-10/month additional |
| Phase 2 (Azure AI Search instead) | ~$74-250/month additional | ~$5-10/month additional | ~$79-260/month additional |
| **Combined (pgvector path)** | **~$150-190/month** | **~$1,120-1,125/month** | **~$1,270-1,315/month** |
| **Combined (Azure AI Search path)** | **~$224-440/month** | **~$1,120-1,125/month** | **~$1,344-1,565/month** |

The gap-analysis/OCR pass in Phase 1 dominates the bill regardless of which Phase 2 retrieval option is chosen — Phase 2 itself is a rounding error on top, unless Azure AI Search is picked, in which case it becomes the second-largest fixed line item after Container Apps + Postgres.
