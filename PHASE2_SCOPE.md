# ISO Certification Platform — Phase 2 Scope: Auditor Copilot (RAG)

## Status
Scope definition. Depends on Phase 1 (`PHASE1_SCOPE.md`) being in place — the copilot retrieves over documents and findings that Phase 1 already ingested and evaluated. Not started.

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
- **Option B: Azure AI Search** — managed indexing/hybrid search/security trimming, but a separate billed service (~$70+/month fixed) and a second data store to keep in sync.
- Recommendation carried over from prior discussion: start with pgvector given current scale; revisit Azure AI Search only if hybrid-ranking, AAD security trimming, or multi-modal indexing become real requirements.

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

---

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

At 100 applications and, say, 500 chat turns/month total: embeddings ≈ $2, chat ≈ $1-2.50. **This entire layer adds well under $10/month in model cost** at this scale — it's the smallest line item in the whole system, cloud infra and Phase 1's OCR usage both dwarf it.

### Combined Phase 2 incremental monthly estimate (100 applications, pgvector chosen)

**~$0 additional infrastructure (same Postgres) + ~$5-10 additional AI usage ≈ under $15/month on top of Phase 1's total.**

If Azure AI Search is chosen instead of pgvector, add its flat ~$74-250/month regardless of usage — this is the single biggest lever in whether Phase 2 is "nearly free" or "a new fixed cost line," which is why pgvector remains the default recommendation at current scale.
