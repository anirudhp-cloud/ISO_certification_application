# ISO/IEC 42001 AI Governance Certification Platform

An AI-assisted audit platform for ISO/IEC 42001 (AI Management System) certification. A
**developer** uploads an organization's AI-governance evidence (policies, risk registers,
process docs); an **auditor** runs an LLM-based gap analysis against the standard's full
Annex A (38 controls) + clauses 4-10 catalog — including Annex B's detailed "Implementation
guidance" per control — and reviews the resulting findings.

- **Backend**: FastAPI + PostgreSQL (Python 3.12)
- **Frontend**: a single static vanilla-JS app (`frontend/`), served by the same backend process — no separate build step or dev server
- **LLM**: Azure OpenAI (GPT-4.1), called directly from the backend — no agent framework
- **OCR (optional)**: Azure AI Document Intelligence, used only as a fallback for scanned PDFs / embedded images

## Prerequisites

- Python 3.12
- PostgreSQL, running and reachable
- An Azure OpenAI resource with a GPT-4.1 deployment (required — the app calls it live, nothing is mocked)
- An Azure AI Document Intelligence resource (optional — only needed for scanned PDFs / embedded-image OCR; native `.txt`/`.docx`/`.pptx`/`.xlsx` and text-layer `.pdf` extraction work without it)

## 1. Configure environment variables

Create `.env` at the **project root** (not inside `backend/`):

```env
LLM_ENDPOINT=https://<your-azure-openai-resource>.cognitiveservices.azure.com/
LLM_API_KEY=<your-azure-openai-key>
LLM_DEPLOYMENT=gpt-4.1
LLM_API_VERSION=2024-10-21

DATABASE_URL=postgresql+psycopg2://<user>:<password>@localhost:5432/iso_certification

JWT_SECRET_KEY=<any-long-random-string>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Optional — only needed for scanned-PDF / embedded-image OCR
DOC_INTELLIGENCE_ENDPOINT=
DOC_INTELLIGENCE_KEY=
```

Never commit this file or share it — it holds live API keys.

## 2. Create the database

```bash
# from psql, or your Postgres client of choice
createdb iso_certification
```

(Match the database name to whatever you put in `DATABASE_URL` above.)

## 3. Set up the backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

## 4. Apply migrations and seed the ISO 42001 catalog

```bash
# still inside backend/, with the venv active
python -m alembic upgrade head
python -m app.seed
```

`app.seed` loads `seed_data/iso42001_requirements.json` (clauses 4-10 + all 38 Annex A
controls, each with its Annex B implementation-guidance checklist) into the database. Re-run
it any time that JSON file changes — it's an idempotent upsert, safe to run repeatedly.

## 5. Run it

```bash
# still inside backend/, with the venv active
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** — this single process serves both the API (`/api/*`) and the
frontend (everything else), so there's nothing else to start.

## Using the app

1. Register (or log in) as a **developer**, either creating a new organization or joining an
   existing one, then select the ISO/IEC 42001 standard and upload documents.
2. Register (or log in) as an **auditor** in the same organization. From there you can:
   - Click **Analyze** on a single document's row for a standalone preview (which Annex A
     controls it maps to + its Annex B guidance checklist) — this never writes to the shared
     findings.
   - Open **Findings → Analyze** to run the full org-wide gap analysis across every current
     document, then open **Gap Analysis** for a filtered view of just the gap/partial
     requirements with their guidance checklists.

## Dev observability

Every real LLM call (map step per document, reduce step per multi-document clause) prints to
the console:
- The exact system + user prompt sent, line-numbered — also saved to `prompt_logs/<timestamp>__<label>.txt` at the project root, one file per call.
- The raw LLM response.
- Token usage and estimated cost (`$` — GPT-4.1 pricing, see `backend/app/ai/pricing.py`).

`backend/tests/test_print_full_prompt.py` dumps the exact system prompt built from the live
database (against a hardcoded sample document) to `full_prompt_iso42001.txt` — useful for
inspecting the catalog/prompt without running a real Analyze:

```bash
cd backend
venv/Scripts/python tests/test_print_full_prompt.py
```

## Project structure

```
backend/
  app/
    api/routes/     FastAPI routers — HTTP in, calls crud/ and ai/, response out
    crud/            Database access functions (one file per entity)
    models/          SQLAlchemy models (the schema)
    schemas/         Pydantic request/response shapes
    ai/              LLM pipeline — clause_mapper (map step), aggregator (reduce step),
                      openai_client (API calls + cost/prompt logging), pricing, cost_tracker
    extraction/      File-parsing — document_extraction.py (format router: txt/docx/pptx/
                      xlsx/pdf), image_extractor.py, document_intelligence_client.py (OCR)
    tasks/           Celery task wrappers (called directly today — no broker running yet)
  alembic/versions/  Database migrations
  prompt_library/    System prompts per standard + the reduce-step prompt
  tests/             Manual inspection scripts (not an automated suite)
seed_data/           The ISO 42001 requirement catalog (source of truth for clauses table)
frontend/            Static vanilla-JS SPA (index.html, app.js, styles.css)
prompt_logs/         Generated at runtime — one file per real LLM call (gitignored-worthy)
```

## Known limitations

- Scanned/image-only PDFs and embedded images (screenshots, scanned pages pasted into a
  `.docx`/`.pptx`/`.pdf`) require `DOC_INTELLIGENCE_ENDPOINT`/`DOC_INTELLIGENCE_KEY` to be
  configured — without it, extraction for those cases is honestly recorded as unavailable
  rather than silently faked, and that content contributes nothing to the analysis.
- Even with Document Intelligence configured, embedded-image OCR text is currently stored
  separately and not yet merged into the text sent to the LLM.
- No background job queue is running yet (Celery/Redis) — extraction and analysis run
  synchronously on the request; fine for demo/dev scale, not for production document volumes.
