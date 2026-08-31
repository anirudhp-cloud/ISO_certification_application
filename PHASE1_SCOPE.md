# ISO Certification Platform — Phase 1 Scope: Compliance Engine

## Status
Scope definition. Builds on the registry design in `ISO42001_Certification_Platform.md` (Part 2) and the ingestion/extraction flow worked out in conversation. No RAG, no copilot — this phase produces structured, human-reviewed compliance findings from uploaded documents.

## Objective
Take a document a developer uploads, work out which clauses of the selected standard it satisfies, surface the gaps, and let an auditor turn that into a reviewed, defensible finding — without any open-ended chat or cross-document retrieval.

## In scope

### 1. Registry & standard selection
- Organizations, users (developer/auditor persona, no RBAC/auth yet) — as already prototyped in `frontend/`. No `applications`/AI-system entity — certification is at the organization level, confirmed.
- Certification-standard selection (ISO 9001 / ISO/IEC 42001 / ISO/IEC 27001) scopes the dashboard directly against `organization_id`.

### 2. Document ingestion
- Three ingestion methods: manual upload, share-path reference, zip upload (extract → one document per file).
- Versioning + soft delete, as defined in the existing `documents` schema.

### 3. Format routing & extraction (built)
- `.txt` → read directly.
- `.docx` / `.pptx` → local structured extraction (`python-docx` / `python-pptx`, no cloud call) — `app/extraction/document_extraction.py`.
- `.pdf` → native text-layer extraction first (PyMuPDF); Azure Document Intelligence (Layout model) only as OCR fallback for scanned/image PDFs. If OCR is needed but no Document Intelligence resource is configured, the extraction is honestly recorded as `ocr_unavailable` rather than silently faked — the upload itself still succeeds.
- Embedded images (tables-as-images inside otherwise-native `.docx`/`.pptx`/`.pdf` files) are pulled out separately (`app/extraction/image_extractor.py`) and OCR'd individually — same graceful `ocr_unavailable`-equivalent (`ocr_text = null`) behavior when Document Intelligence isn't configured.
- Result persisted as a `document_extractions` row per document version (+ `document_extracted_images` rows for embedded images) — `app/tasks/extract_document.py`'s `run_extraction`, called synchronously right after upload/share-path/zip/new-version for now (no Redis running locally yet; the Celery task wrapper exists so switching to `.delay()` later is a one-line change). Extraction failure never blocks the upload it's attached to. Readable via `GET /api/documents/{id}/extraction`.

### 4. Standards & clause catalog (new)
- `standards` (ISO 9001 / 42001 / 27001) and `clauses`/`controls` tables — the fixed reference data the LLM pass evaluates documents against.

### 5. Clause-mapping / gap analysis (LLM pass) — built
- GPT-4.1 mini, one call per document per standard — the system prompt for the document's standard (`prompt_library/system_prompt_42k.py` / `_27k.py` / `_9k.py`) carries the full clause+control list for that standard alone (see the framework-isolation rule in `ISO42001_Certification_Platform.md` Gap Analysis section).
- Structured JSON output (matches `app/ai/schemas.py` `MappingResult`): a list of `{ requirement_code, relevance_score (0-100), coverage_score (0-100), rationale }` — `rationale` must quote the exact source passage. Scores are chosen over a status label (met/partial/gap) because they preserve more information: an auditor can always bucket a score into a label, but a label can't be un-bucketed back into a score, and the override flow needs before/after scores (`previous_relevance_score`/`previous_coverage_score`), not before/after labels.
- Auditor-triggered, not automatic on upload: `POST /organizations/{id}/standards/{standard}/analyze` (`app/tasks/run_gap_analysis.py`) does a full recompute — map step (`app/ai/clause_mapper.py`) over every active document, then a reduce/combine step (`app/ai/aggregator.py`) per clause that merges 2+ contributing documents' evidence into one finding via a second LLM call (`prompt_library/reduce_prompt.py`) when a requirement's evidence is split across documents.
- Long documents handled by deterministic map-then-merge chunking (splitting to fit the context window), not similarity search — no embeddings needed for this pass.

### 6. Findings & human review — built
- `findings` table: one row per (organization, clause), holding current status, evidence references (`evidence_document_id` for the primary contributor, `evidence_document_ids` for the full combined set — see `DATABASE_DESIGN.md` §5), and score/rationale.
- Findings land as drafts (`mapping_method='auto'`); an auditor confirms or overrides each one via `PATCH /findings/{id}` (`app/api/routes/findings.py`) — auditor-only, `403` for a developer. A finding already confirmed/overridden is never touched by a later analysis re-run.
- Aggregated per-organization, per-standard readiness score via `GET /organizations/{id}/standards/{standard}/report` (e.g. "1 met / 2 partial / 35 gap out of 38 controls").

### 7. Reporting
- Export a per-organization, per-standard compliance readiness report (clause-by-clause status + evidence citations + open gaps).

## New data introduced in Phase 1 (schema detail pending)
- `standards`, `clauses`
- `document_extractions`
- `findings`

## API surface (Phase 1)
- `POST /api/organizations/{id}/standards/{standard}/documents` (upload / share-path / zip variants)
- `GET /api/organizations/{id}/standards/{standard}/documents`
- `POST /api/documents/{id}/comments`, `GET /api/documents/{id}/comments`
- `GET /api/documents/{id}/extraction` (built)
- `POST /api/organizations/{id}/standards/{standard}/analyze` — auditor-only; triggers the full map+reduce clause-mapping pass (built)
- `GET /api/organizations/{id}/standards/{standard}/findings` (built)
- `PATCH /api/findings/{id}` — auditor confirm/override (built)
- `GET /api/organizations/{id}/standards/{standard}/report` (built)

## UI surface (Phase 1)
- Existing mockup screens (user switch, standard select, organization documentation view, document upload tabs, version history, comments).
- New: Findings review screen (per-organization, per-standard clause list with status, evidence, accept/override controls) and a report view/export.

## Explicitly out of scope for Phase 1
- Embeddings, vector search, RAG.
- Auditor copilot chat, cross-document semantic search, version-diff assistant.
- Continuous monitoring, OCR/vision compliance scanning (deepfake/PII-in-image), sector packs, SharePoint/Jira integration — see Phase 2 doc and beyond.
- Fine-grained RBAC (permission matrices beyond the developer/auditor persona check already enforced on individual endpoints) — authentication itself is no longer deferred, see below.

## Authentication (built, no longer deferred)
Real registration/login: `POST /api/auth/register`, `POST /api/auth/login`. Passwords are bcrypt-hashed (`passlib`) and never decrypted — login re-hashes the submitted password and compares hashes. Both endpoints issue a signed JWT (`app/security.py`, `HS256`, expiry from `JWT_EXPIRE_MINUTES`); every write endpoint requires it via `app/deps.py`'s `get_current_user`, which verifies the signature and expiry before trusting the user id inside it. There is no plain "list all users" endpoint (would leak every email with no access control) — document/comment responses instead carry a denormalized display name (`submitted_by_name`, etc.) computed server-side.

## Exit criteria
A developer can upload documents for an application, an LLM pass produces draft clause findings, an auditor reviews/accepts them, and a readiness report can be generated — end to end, without any conversational or retrieval component.

---

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

Per the detailed sensitivity analysis worked out earlier (40 documents/application, 40 pages/document, mixed scan rate and embedded-image density):

| Scenario | Est. cost/application | At 100 applications | At 500 applications |
|---|---|---|---|
| Best case (mostly native docs, few embedded images) | ~$4.75 | ~$475 | ~$2,375 |
| Baseline (40% scanned, 10 embedded images/doc) | ~$11.15 | ~$1,115 | ~$5,575 |
| Worst case (mostly scans, image-heavy) | ~$20-37 | ~$2,000-3,700 | ~$10,000-18,500 |

Document Intelligence OCR (whole-page + embedded-image) dominates this line, not GPT-4.1 mini — see the format-routing design above for why minimizing unnecessary OCR calls is the highest-leverage cost control here.

### Combined Phase 1 monthly estimate (baseline scenario, 100 applications)

**~$150-190 (infrastructure) + ~$1,115 (AI/OCR) ≈ $1,265-1,305/month**

Infrastructure is a small, fairly fixed slice of the total; AI/OCR usage is the variable that actually moves with your document volume and content mix.
