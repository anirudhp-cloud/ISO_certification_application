# ISO 42001 Platform — Stage 1 Implementation Plan

**Date:** 27 August 2026
**Product decision:** this is a **document-mapping tool** for **Stage 1 (documentation review)**.
Not an AI management system. Not Stage 2.

---

## 1. What we are building

For every submitted document, produce an explicit **clause structure** and **control structure**,
each backed by a verbatim quote and a human-verifiable location.

```
CLAUSES SATISFIED — 3 of 32
  5.2  AI policy                                      90%
       "This Artificial Intelligence Policy sets forth TechVest Global's…"
       → Section "1. Purpose", paragraph 1

CONTROLS SATISFIED — 2 of 38
  A.2.2  AI policy                                    75%
         "All AI activities… shall be guided by the following core principles."
         → Section "4. AI Principles", paragraph 1
         Annex B points not satisfied (2 of 12):
           · processes for handling deviations and exceptions to policy
           · informed by the level of risk posed by the AI systems
```

### Scope boundary — state this in the UI

The tool reviews **documents only**. It does not sample records, interview staff, or observe
practice. Its output is a **documentary review**, not a conformity determination. Stage 2 is
out of scope by design.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Requirement** | One catalog row. Either a **clause** (32, codes 4.1–10.2) or a **control** (38, codes A.2.2–A.10.4) |
| **Evidence** | A **verbatim passage** from a document plus its location. The document itself is not evidence |
| **Mapping** | One link: this passage, in this document, supports this requirement, to this degree |
| **Finding** | A requirement-level rollup **confirmed by an auditor**. The machine produces mappings, not findings |

The last row matters: the current schema calls machine output `findings`, which overloads an
audit term of art. Machine output is an **evidence mapping**.

---

## 3. Why clauses and controls are separated

| | Clauses 4–10 (32) | Annex A controls (38) |
|---|---|---|
| Status | Mandatory requirements | Normative catalog of risk-treatment options |
| Exclusion | **Never permitted** | Permitted, with documented justification |
| Annex B guidance | None | 248 guidance points |
| Reference artifact | `ISO_42001_Mandatory_Clauses_Mapping…xlsx` | `35.Statement_of_Applicability…xlsx` |

Controls do not map one-to-one to clauses. Per clause 6.1.3, Annex A is compared against as a
whole and the result is the Statement of Applicability. **No clause↔control mapping table will
be built** — it does not exist normatively.

Without a risk register, applicability justification is **auditor-asserted text**, not
system-derived. Do not claim otherwise.

---

## 4. The pipeline

```
UPLOAD TIME  (exists today)
   document uploaded
        ▼
   extract_text()  →  flat text  +  position-tagged chunks
        ▼
   document_extractions

ANALYZE TIME
   auditor clicks Analyze
        ▼
   per document, TWO LLM calls:
        clause pass   → 32 clauses,  ~3,500 token catalog,  no Annex B
        control pass  → 38 controls, ~10,900 token catalog, Annex B included
        ▼
   validate returned codes against catalog (log + drop unknowns)
        ▼
   locate_quote(rationale, chunks)   ← deterministic, no LLM
        ▼
   evidence_mappings rows  (segment = 'clause' | 'control')

OUTPUT
   GET /documents/{id}/mappings  →  two-section view
```

Two LLM calls **per document**, not two in total.

### Token cost of splitting: +3.8%

The **catalogue** splits for free:

| Catalogue only | Tokens |
|---|---|
| All 70 together | 14,351 |
| Clauses only (32) | 3,472 |
| Controls only (38, with Annex B) | 10,884 |
| Two segments combined | 14,356 |

But each pass carries its own ~2,000-character instruction preamble, so the preamble is
duplicated. Measured against the real DB catalogue after implementation:

| Whole system prompt | Tokens |
|---|---|
| Old single pass | 15,451 |
| **New two passes combined** | **16,040** |
| **Delta** | **+589 (+3.8%)** |

*(An earlier draft of this plan claimed "five tokens more". That figure was the catalogue
comparison only and understated the real cost.)*

Both prefixes are still cacheable, so the marginal billed cost is lower again. In exchange the
clause pass stops carrying ~15 lines of Annex B instructions that never apply to clauses, and
stops being asked for a field that is always empty for clauses.

### LLM output contract

Clause pass — four fields per mapping:

```json
{ "mappings": [
  { "requirement_code": "5.2", "relevance_score": 95, "coverage_score": 90,
    "rationale": "<verbatim quote from the document>" }
] }
```

Control pass — the same four plus unmet Annex B points, copied verbatim from the catalog:

```json
{ "mappings": [
  { "requirement_code": "A.2.2", "relevance_score": 95, "coverage_score": 75,
    "rationale": "<verbatim quote>",
    "unmet_guidance_points": ["The AI policy should include processes for handling deviations and exceptions to policy."] }
] }
```

Requirements the document says nothing about are **omitted**, not scored zero.

### Why the quote is mandatory

The model is never asked where a passage sits. It is required to quote verbatim; the code then
locates that quote against the stored chunks (`app/ai/source_locator.py`). A model cannot
fabricate a page reference through this path.

---

## 5. Schema changes — minimal set

One new table and one new column deliver the whole feature. Everything else is deferred.

### Now (M1–M2)

```sql
ALTER TABLE clauses ADD COLUMN sort_order integer;   -- fixes clause 10 sorting before clause 4

CREATE TABLE evidence_mappings (
  id                    uuid PRIMARY KEY,
  run_id                uuid NOT NULL,               -- plain UUID; becomes an FK at M4
  document_id           uuid NOT NULL REFERENCES documents(id),
  clause_id             uuid NOT NULL REFERENCES clauses(id),
  segment               varchar(10) NOT NULL,        -- 'clause' | 'control'
  relevance_score       numeric(5,2),
  coverage_score        numeric(5,2),
  rationale             text,                        -- the verbatim quote
  source_location       varchar(160),                -- computed at WRITE time
  unmet_guidance_points text[],
  created_at            timestamptz NOT NULL DEFAULT now(),
  UNIQUE (run_id, document_id, clause_id)
);
CREATE INDEX ix_evidence_mappings_run_segment ON evidence_mappings (run_id, segment);
CREATE INDEX ix_evidence_mappings_document   ON evidence_mappings (document_id);
```

### At M4 (the gate)

`analysis_runs` — thin, job state only: status, triggered_by, timestamps, prompt versions,
model id, token counts, cost, gate override fields. Coverage is **derived by query**, never
stored.

### At M5 (grading)

Columns on `findings`: `analysis_run_id`, `is_applicable` (controls only, NULL for clauses),
`applicability_note`, `proposed_grade`, `grade`. No new table.

### Explicitly deferred until M3 has been used

`audits`, `nonconformities`, `corrective_actions`. Correct for audit-workflow fidelity, not
required for the deliverable, and most likely to change shape once a real auditor uses the tool.

### Dropped from earlier drafts

- `evidence_state` column — derivable via `EXISTS` against `evidence_mappings`
- stored coverage — derivable via `GROUP BY clause_id`
- any clause↔control mapping table — not normative

---

## 6. Grading (M5)

First and cheapest: separate the two states that currently look identical.

| State | Meaning |
|---|---|
| `no_evidence` | nothing submitted yet |
| `insufficient` | submitted and inadequate |

Then replace the `70 / 30 → met / partial / gap` rubric with what a certification body issues,
as a **proposed** grade an auditor confirms:

| Condition | Proposed grade |
|---|---|
| Control, `is_applicable = false` | `not_applicable` |
| No evidence — clause | `major_nc` |
| No evidence — control | `minor_nc` |
| Coverage ≥ 90, no unmet Annex B points | `conforming` |
| Coverage ≥ 90, some unmet points | `ofi` |
| Coverage 50–89 | `minor_nc` |
| Coverage < 50 — clause | `major_nc` |
| Coverage < 50 — control | `minor_nc` |

Thresholds move to `config.py`. Controls never propose `major_nc`: severity depends on the risk
a control treats, and there is no risk register.

---

## 7. Milestones

| # | Milestone | Days | Ships something usable |
|---|---|---|---|
| **M0** | **Fix docx/pptx extraction + re-extract existing documents** | **1** | Correct citations |
| M1 | `sort_order`, requirement-code validation, prompt split | 1 | No — enabling |
| M2 | Two-pass pipeline + `evidence_mappings` + tests | 2–3 | No — no UI yet |
| M3 | Per-document clause/control view (API + UI) | 1.5–2 | **Yes — the deliverable** |
| | **Subtotal** | **≈ 6 days** | |
| M4 | Gate: `analysis_runs`, background job, coverage screen, override | 3 | Yes |
| M5 | Grading, applicability, two-tab findings page | 3 | Yes |
| | **Total** | **≈ 12 days** | |

M0 must precede M2. M3's entire value is citations; shipping it on wrong locations would be
worse than not shipping it.

---

## 8. M0 — extraction defects (measured, not inferred)

Reproduced against `storage_data/…/v1_2A.AI_Policy for TechVest.docx`.

### Defect 1 — paragraph numbers drift up to +33

`_extract_docx` increments its counter only for non-empty paragraphs. The file has **85 body
paragraphs, 51 non-empty** — 34 blanks. The drift compounds:

| Cited as | Actually is | Drift | Text |
|---|---|---|---|
| Paragraph 1 | 2 | +1 | AI POLICY FOR TECHVEST |
| Paragraph 20 | 39 | +19 | AI model design, development, training… |
| Paragraph 30 | 50 | +20 | 3. Leadership Commitment |
| Paragraph 40 | 70 | +30 | 5. Roles and Responsibilities |
| Paragraph 51 | 84 | +33 | Any amendments to this Policy shall… |

### Defect 2 — every table is relocated to the end of the document

The current code emits all paragraphs, then all tables. True body order in this file:

```
p p p p p T p T p p T p p p … p T p T p T p T p T p T p T p p p p T p p p …
          ↑ first table sits at body position 6 of 97
```

**12 tables**, interleaved. Because `text = "\n".join(c["text"] for c in chunks)`, this
scrambled order is also what the LLM reads. For a document set built on SoA sheets, risk
registers and roles matrices, that is most of the substance arriving out of place.

### Defect 3 — heading context discarded

The file carries **8 × Heading 1 and 4 × Heading 2** with numbered titles
("3. Leadership Commitment", "5. Roles and Responsibilities"). None is captured.

This is the deeper issue: **Word displays no paragraph numbers**, and a `.docx` has no fixed
pagination, so even a correct paragraph count is unverifiable by a human. A heading is
searchable with Ctrl+F.

### Defect 4 — headers and footers skipped

`doc.paragraphs` returns body paragraphs only. Controlled-document IDs, versions and
classification often live in headers. (Not present in this particular file.)

### Defect 5 — merged table cells duplicated

`row.cells` yields one entry per grid column, so a merged cell repeats in the row text.

### The fix

Walk the body in true document order and cite by heading:

```python
for child in doc.element.body.iterchildren():
    if child.tag == qn('w:p'):     # paragraph, in real position
    elif child.tag == qn('w:tbl'): # table, in real position
```

- preserve order for both the chunks **and** the flat text sent to the LLM
- track the current heading; emit `Section "5. Roles and Responsibilities", paragraph 3`
- tables as `Section "…", table 2, row 4`
- de-duplicate merged cells by underlying `tc` element
- extract headers and footers
- same reading-order treatment for `.pptx` (currently z-order)

### Two consequences

1. **Existing extractions are already wrong in the database.** Extraction runs at upload
   (`api/routes/documents.py:41`), so every stored docx has bad chunks. M0 includes a backfill
   that re-runs `run_extraction` over existing documents. No LLM calls, no cost.
2. **The flat text changes, so LLM results change.** Any analysis run before M0 is not
   comparable to one after. Re-analysis is needed after the backfill — cheap now, expensive later.

---

## 9. Detailed change list

### M0 — completed 27 Aug 2026

**Edited**
- `app/extraction/document_extraction.py` — rewrote `_extract_docx` to walk
  `body.iterchildren()` in reading order and cite by heading; added `_docx_row_text`
  for merged-cell de-duplication; header/footer extraction; reading-order sort for
  `_extract_pptx` (was z-order)
- `app/models/document_extraction.py` — `cascade="all, delete-orphan"` on
  `extracted_images` (see the extra defect below)
- `requirements.txt` — added `pytest==9.1.1`, which was never declared

**New**
- `scripts/reextract_documents.py` — backfill, with `--dry-run` and `--ext`
- `tests/test_extraction_docx.py` — 9 tests: table position preserved, control table
  before first heading, flat text order, heading-scoped paragraph numbering that
  restarts per heading, blank paragraphs dropped, merged cells de-duplicated, header
  text captured, and an end-to-end `locate_quote` check

**Extra defect found and fixed — re-extraction had never worked.**
`save_extraction` replaces a prior attempt with `db.delete(existing)`, but
`extracted_images` carried no cascade, so SQLAlchemy nulled the children's FK
instead of deleting them and hit
`document_extracted_images.document_extraction_id`'s NOT NULL constraint. Any
re-extraction of an existing document failed. Fixed at the relationship; no
migration needed.

**Verified against the real file** (`v1_2A.AI_Policy for TechVest.docx`): 77 chunks,
all 12 tables emitted in position — the document-control block (Document ID
`AIMS-QMS-D-02A`, version, classification, approval and revision tables) now sits at
chunks 4–15 where it belongs, instead of after all 51 paragraphs. Backfill run;
citations resolve from the persisted chunks:

```
"This Policy shall be reviewed at least annually"  → Section "7.  Policy Review and Maintenance", paragraph 1
"The AI Management System (AIMS) applies to all…"  → Section "2.  Scope of the AI Management System", paragraph 1
"AIMS-QMS-D-02A"                                    → Table 1, row 2
```

**Note:** `tests/test_print_full_prompt.py` is a script, not a test — it defines only
`main()` and pytest never collects it. Left as-is.

### M1 — completed 27 Aug 2026

**New**
- `alembic/versions/d3e4f5a6b7c8_add_clause_sort_order.py` — adds the column and
  backfills it in SQL (clauses before controls, then by numeric code segments), so it
  could be made NOT NULL without requiring a re-seed first
- `prompt_library/system_prompt_42k_clause.py` — clause prompt, `VERSION = "iso42001-clause-v1"`
- `tests/test_prompt_segments.py` — 15 tests

**Edited**
- `app/models/clause.py` — `sort_order`
- `app/seed.py` — `sort_order` from the seed file's own sequence
- `app/crud/finding.py:43` — `order_by(Clause.sort_order)`
- `prompt_library/system_prompt_42k.py` → `_control.py` — scoped to Annex A only
  ("Clauses 4-10 are NOT in scope for this pass"), `VERSION = "iso42001-control-v1"`
- `prompt_library/system_prompt_27k.py`, `_9k.py` — `VERSION` added
- `prompt_library/__init__.py` — registry keyed by `(framework, segment)`, plus
  `has_segment()`; `get_system_prompt(standard_id, segment) -> (prompt, version)`
- `app/ai/requirement_catalog.py` — `split_by_segment()`, and
  `format_requirements_listing(clauses, segment)` which omits the Annex B block for clauses
- `app/ai/schemas.py` — `SegmentedMapping` (clauses / controls / prompt_versions)
- `app/ai/openai_client.py` — `get_control_mappings(..., segment)` returns
  `(result, prompt_version)`; prompt logs now labelled `map_clause__` / `map_control__`
- `app/ai/clause_mapper.py` — **two LLM calls per document**; `_keep_known_codes()` drops
  and logs codes outside the segment's catalogue
- `app/tasks/run_gap_analysis.py` — consumes `SegmentedMapping.all_mappings()`
- `app/api/routes/analyze.py` — **deleted the unauthenticated `POST /api/analyze`**
  (nothing referenced it; it required no login and spent tokens on arbitrary input)

**Verified:** migration applied on top of `b2c3d4e5f6a7`; 70 catalog rows now order
`4.1 … 10.2, A.2.2 … A.10.4`; app imports clean; 24 tests pass.

**Note:** ISO 27001 keeps its single combined prompt registered for both segments (it
has both, but hasn't been split yet) and ISO 9001 registers a clause segment only,
having no Annex A. Neither is exercised — only `iso42001_requirements.json` is seeded —
and `map_document` skips any segment with an empty catalogue.

### M2 — completed 27 Aug 2026

**New**
- `alembic/versions/e4f5a6b7c8d9_add_evidence_mappings.py` — the table, with a
  `segment IN ('clause','control')` check constraint and both indexes
- `app/models/evidence_mapping.py`
- `app/crud/evidence_mapping.py` — `record_mappings()` (resolves each citation at
  write time), `list_for_document()`, `latest_run_id_for_document()`,
  `contributing_document_counts()` (the coverage report, derived not stored),
  `delete_run()`
- `tests/test_pipeline.py` — 12 tests with the LLM client stubbed

**Edited**
- `app/models/__init__.py` — registered `EvidenceMapping`
- `app/tasks/run_gap_analysis.py` — generates a `run_id`, persists each document's
  two segments, one commit for the run's evidence before the rollup, returns the
  `run_id`; log line now reports evidence-mapping count and `N of 70` coverage

**Note on `source_location`:** now resolved at write time onto `evidence_mappings`, so
a citation belongs to its run and can't change if the document is re-extracted later.
`findings` keeps its existing read-time `_compute_source_location` path for now —
that becomes redundant once findings derive from `evidence_mappings`.

**Verified end to end** against the real database with the LLM stubbed (no API calls),
using the TechVest AI Policy:

```
run_id: 53cc6b0c-…
  CLAUSES (2)
    4.3    cov=78.0  -> Section "2.  Scope of the AI Management System", paragraph 1
    5.2    cov=78.0  -> Section "1.  Purpose", paragraph 1
  CONTROLS (2)
    A.2.2  cov=78.0  -> Section "4.  AI Principles", paragraph 1
           unmet: ['The AI policy should be informed by business strategy.']
    A.2.4  cov=78.0  -> Section "7.  Policy Review and Maintenance", paragraph 1
coverage: 4 of 70 requirements have evidence
```

Rows land with the right segment, in catalogue order, with heading-scoped citations —
the M0 extraction fix showing up in the output. Stub rows were then deleted; the 3
auditor-reviewed findings were left untouched, and the 4 unreviewed findings the stub
run had overwritten were removed so nothing carries fake scores. Migration head is
`e4f5a6b7c8d9`; 36 tests pass.

### M3 — completed 27 Aug 2026

**New**
- `app/schemas/evidence_mapping.py` — `RequirementMappingRead`, `SegmentMappingsRead`,
  `DocumentMappingsRead`
- `GET /documents/{id}/mappings` in `app/api/routes/documents.py`, with an optional
  `run_id` to read an earlier run
- `app/crud/evidence_mapping.py` — added `latest_run_for_organization()`
- `tests/test_document_mappings.py` — 7 tests

**Edited**
- `frontend/index.html` — mappings modal (`modal-wide`)
- `frontend/app.js` — `openMappingsModal()` / `renderMappings()` / `renderSegment()` /
  `renderRequirement()`; a **Requirements** button on each document row; plus an
  `escapeHtml()` helper, since the modal renders verbatim quotes lifted out of
  uploaded documents and the codebase had no escaping at all
- `frontend/styles.css` — ~120 lines for the two-section view

**Design change found while building: three states, not two.**
The response carries an explicit `status`, because two of the three show no
requirements and mean opposite things to whoever uploaded the file:

| `status` | Meaning |
|---|---|
| `not_analysed` | no run has read this document yet |
| `no_match` | read in full, supports nothing — misfiled, wrong standard tag, or no extractable text |
| `matched` | supports at least one requirement |

The first implementation could not tell `no_match` from `not_analysed`: a document the
LLM found nothing in produces **zero rows**, so nothing on the document points at a
run. `latest_run_for_organization()` infers it by comparing the organization's most
recent run against the document's `submitted_at`. That is an inference, not a record —
it cannot see a run that produced no rows for *any* document. `analysis_runs` (M4)
makes it authoritative by listing the documents each run actually read.

**Verified over HTTP** against the real database with the LLM stubbed:

```
AI Policy document  v1  status=matched
CLAUSES — 1 of 32
  5.2    AI policy                    75%   -> Section "1.  Purpose", paragraph 1
CONTROLS — 2 of 38
  A.2.2  AI policy                    75%   -> Section "4.  AI Principles", paragraph 1
         Annex B not satisfied (1 of 12):
           · The AI policy should include processes for handling deviations and exceptions to policy.
  A.2.4  Review of the AI policy      75%   -> Section "7.  Policy Review and Maintenance", paragraph 1
```

All three states were exercised directly. Stub rows deleted afterwards; the 3
auditor-reviewed findings left untouched. 43 tests pass.

### M4 + M5 — completed 27 Aug 2026

**New**
- `alembic/versions/f5a6b7c8d9e0_add_analysis_runs_and_grading.py` — `analysis_runs`,
  promotes `evidence_mappings.run_id` to a real FK, and adds the finding grading
  columns. Pre-existing evidence rows are deleted rather than left pointing at runs
  that were never recorded.
- `app/models/analysis_run.py`, `app/crud/analysis_run.py` (`coverage_report`,
  `read_this_document`), `app/schemas/analysis_run.py`
- `app/ai/grading.py` — `propose_grade`, `evidence_state`, `blocks_certification`
- `tests/test_gate.py` (9), `tests/test_grading.py` (14)

**Edited**
- `app/tasks/run_gap_analysis.py` — split into `start_run()` (maps, persists, reports
  coverage, writes **no** findings) and `accept_run()` (the gate; rolls up into
  findings), plus `GateNotSatisfied`
- `app/api/routes/analyze.py` — `POST .../analyze`, `GET /runs/{id}`,
  `POST /runs/{id}/accept` (409 when incomplete without a reason)
- `app/crud/finding.py` — `set_applicability()`, grade wiring, and the stale-review fix
- `app/api/routes/findings.py` — grade/evidence-state fields, grade counts with a
  separate `blocking` total, `PATCH /findings/{id}/applicability`
- `app/config.py` — grading thresholds
- `frontend/` — coverage-gate modal with override reason, clause/control tabs, grade
  badges (dashed while unconfirmed), stale-evidence and exclusion notes

**Background execution deferred, deliberately.** Redis isn't running, so `.delay()`
would fail. Execution stays inline — the same pattern extraction already uses. The
gate doesn't depend on it: it needs the run to persist between two requests, which it
does either way. Switching is a one-line change once a broker is up.

**Grading is asymmetric by segment**, verified across all 70 requirements: 30 clauses
with no evidence propose `major_nc` (blocking), while 36 controls with no evidence cap
at `minor_nc` — severity of a control gap depends on the risk it treats, and there is
no risk register, so calling it major would invent severity. No control ever proposes
`major_nc`; a test asserts this across the whole coverage range.

**Verified over HTTP** with a real LLM run (1 document, $0.052):

```
POST analyze            -> 200  coverage_ready   clauses 14/32  controls 3/38  complete=False
POST accept (no reason) -> 409  53 requirement(s) have no evidence
POST accept (w/ reason) -> 200  70 graded: conforming=4 minor_nc=48 major_nc=18 blocking=18
```

Applicability rules verified: allowed on a control (regrades to `not_applicable`),
refused on clause 5.2 as mandatory, refused without a justification. Stale-review fix
verified: an approved finding kept its auditor grade while raising
`evidence_changed_since_review`.

### Citation resolution — a real bug the live run exposed

The real run resolved only **8 of 17 citations**. All 9 failures were quotes that *are*
in the document but span chunk boundaries: the model quotes a heading plus the
paragraphs beneath it (up to 1,180 characters), while chunks are one paragraph or table
row each, and `locate_quote` only searched quote-inside-chunk.

`app/ai/source_locator.py` now also matches **chunk-inside-quote**, citing where the
passage starts, with a 25-character floor so an incidental short line can't win. Same
quotes, same chunks, no new API calls: **17 of 17**. Stored citations backfilled; 5
regression tests added.

This mattered more than its size suggests — citation is the whole value of the
per-document view, and half of them were silently missing.

**Totals for M0–M3:** ~22 files (9 new, 13 edited), two migrations, one new table, one new column.

---

## 10. API surface (M3–M5)

```
GET    /documents/{id}/mappings                   ← the deliverable (M3)
POST   /audits/{id}/runs                          → { run_id }            (M4)
GET    /runs/{id}                                 status + coverage       (M4)
POST   /runs/{id}/accept                          the gate                (M4)
```

`POST /organizations/{id}/standards/{std}/analyze` remains as a shim so the existing Analyze
button keeps working. The unauthenticated `POST /api/analyze` is deleted.

---

## 11. Known risks

**No test coverage.** `backend/tests/` holds one file that prints a prompt. M2 rewrites the
pipeline with no regression net. Tests are costed into M0 and M2.

**Auth — CLOSED 27 Aug 2026.** See section 14.

**Reviewed findings currently freeze.** `upsert_finding_from_mapping` and
`reset_finding_if_auto` both skip `mapping_method == 'reviewed'`, so an approved finding keeps
citing deleted evidence. Fixed in M5 by raising `evidence_changed_since_review`.

---

## 12. Deferred, with reasons

| Item | Reason |
|---|---|
| `ai_systems`, `risks`, `risk_treatments` | AI management system scope, not document mapping |
| `impact_assessments` (AIIA) | Same |
| `nonconformities`, `corrective_actions` | Correct for audit workflow; shape unknown until M3 is used |
| `audits` | Not needed for the deliverable |
| Auditor working sheet | Separate feature |
| Stage 2 — sampling, interviews | A document tool cannot support it |
| Clause↔control mapping table | Not normative; controls map to risks |

---

## 13. Progress

| Milestone | Status |
|---|---|
| M0 — extraction fix | **Done — 27 Aug 2026** |
| M1 — foundation | **Done — 27 Aug 2026** |
| M2 — two-pass pipeline | **Done — 27 Aug 2026** |
| M3 — per-document view | **Done — 27 Aug 2026** |
| M4 — gate | **Done — 27 Aug 2026** |
| M5 — grading | **Done — 27 Aug 2026** |
| Auth hardening | **Done — 27 Aug 2026** |
| Assessment made auditor-only | **Done — 27 Aug 2026** |
| Run resilience (40-document readiness) | **Done — 31 Aug 2026** |


---

## 14. Auth hardening — completed 27 Aug 2026

### What was wrong

**No tenant isolation at all.** `user.organization_id` was never compared against the
organization named in a request — not once, anywhere in the codebase. Isolation rested
entirely on the frontend choosing which UUID to send, so any authenticated user could
read, write or delete another organization's evidence by editing the URL.

**Seven endpoints required no login**, with no global middleware to catch them:
document list, document versions, **full extracted document text**, clause/control
mappings, findings, findings report, and review comments.

**`DELETE /documents/{group}`** authenticated but checked neither persona nor
organization.

### The guards

Added to `app/deps.py`, applied as FastAPI dependencies so a route depends on the guard
*instead of* `get_current_user` and the check can't be forgotten per-route:

| Guard | For routes keyed by |
|---|---|
| `require_org_access` | `organization_id` in the path |
| `require_document_access` | a single `document_id` |
| `require_document_group_access` | a `document_group_id` (version history) |
| `require_run_access` | an `analysis_run` id |

The rule: **auditors work across organizations by design** (they pick one from the
organizations list); **developers are confined to their own**. A missing document, group
or run is 404 regardless of whether the caller would have been allowed to see it — the
alternative leaks existence — and the 403 message never names the organization, so
UUIDs can't be probed for enumeration.

`GET`/`POST /api/organizations` remain deliberately pre-auth: the registration screen
populates its dropdown from them before any token exists, and `OrganizationRead`
exposes only id, name and created_at.

### Also fixed: 401 vs 403

`HTTPBearer` defaults to 403 for a *missing* Authorization header. The frontend treats
401 as "session gone, log out" and 403 as "you may not do this", so a missing token
returning 403 meant no auto-logout on an expired session. Now `auto_error=False` with an
explicit 401.

### Verified live — cross-tenant attempt

A real developer token from a different organization, against another organization's
data:

```
target                       no token   other-org dev   auditor
document list                     401             403       200
FULL DOCUMENT TEXT                401             403       200
clause/control mappings           401             403       200
version history                   401             403       200
review comments                   401             403       200
findings                          401             403       200
findings report                   401             403       200

DELETE victim's documents as other-org developer -> 403
```

No regression: the same developer against their **own** organization returns 200 on all
seven. A structural test walks every route in `app/api/routes/` and fails if any is
neither guarded nor on the pre-auth allowlist, so a new route can't quietly ship open.

**80 tests pass** (12 tenant-isolation).

### Still open, deliberately

- Delete permission is org-scoped but not role-scoped — any member of the owning
  organization can delete its documents. Who *should* be allowed to is a product
  decision, not a security gap.
- Background execution still inline; needs Redis.
- Pre-existing unescaped interpolation elsewhere in `frontend/app.js` (document names in
  the tables). The mappings and findings views escape; the older tables do not.


---

## 15. Assessment surfaces made auditor-only — 27 Aug 2026

### What was wrong

Assessment was reachable by developers. The **Requirements** button rendered for every
persona (`app.js` — unlike the adjacent Reupload/Delete, which are gated), and
`require_document_access` admits the owning organization's developer, so a developer
saw coverage percentages, per-requirement scores and unmet Annex B points.

Worse, and pre-dating this work: `SIDEBAR_ITEMS` had **Findings** and **Gap Analysis**
at `auditorOnly: false`. A developer could already open all 70 requirements with their
grades, and the per-control Annex B checklist. Only Review and Organizations were
gated. So hiding one button would have been cosmetic.

### Why it matters

The scores are **unreviewed model output**. Shown to whoever submitted the document
they imply a verdict no auditor has issued, and they invite wording tuned until the
number rises — which corrupts the evidence. In a real audit the auditee never sees the
auditor's working papers before a decision; they see the findings the auditor issues.

### The change

Three composable guards in `app/deps.py` — `require_auditor`,
`require_auditor_org_access`, `require_auditor_document_access`. They compose *onto*
the tenant guards rather than replacing them, so the organization check still runs;
that matters if the auditor rule is ever narrowed to assigned organizations, where a
persona check alone would silently stop being sufficient. A test asserts the
composition holds.

| Surface | Before | After |
|---|---|---|
| `GET /documents/{id}/mappings` | any org member | **auditor only** |
| `GET .../findings` | **unauthenticated** | **auditor only** |
| `GET .../report` | **unauthenticated** | **auditor only** |
| `POST .../analyze` | auditor (inline check) | auditor (dependency) |
| Findings page | all personas | **auditor only** |
| Gap Analysis page | all personas | **auditor only** |
| Requirements button | all personas | **auditor only** |

`analyze.py`'s inline `_require_auditor` helper was removed in favour of the
dependency, so the rule lives in one place.

**Developers keep** their own documents, extracted text, version history and review
comments — otherwise they couldn't see what they submitted at all. A test names those
four routes and fails if any becomes auditor-gated.

### Verified over HTTP

Own-organization developer vs auditor, same organization:

```
endpoint                   kind          own-org dev   auditor
requirements (mappings)    assessment            403       200
findings                   assessment            403       200
findings report            assessment            403       200
own document list          developer's           200       200
own document text          developer's           200       200
own version history        developer's           200       200
review comments            developer's           200       200

POST analyze as developer -> 403
```

**84 tests pass** (16 tenant-isolation and persona).

### Consequence to accept

The developer is now back to submitting without feedback — the problem raised at the
start of this work. A misfiled or wrongly-tagged document produces no signal until an
auditor says so. That was the explicit trade-off in choosing full separation; a
status-only developer view (read / matched nothing / matched N) would close it without
exposing any assessment detail, if it's wanted later.


---

## 16. Run resilience — 40-document readiness, 31 Aug 2026

### Measured capacity, from two real runs

| Documents | Wall time | Input tokens | Cached | Cost |
|---|---|---|---|---|
| 1 | 26.9s | 15,557 | 0 | $0.0522 |
| 2 | 42.3s | 29,340 | **27,136** | $0.0515 |

Marginal: **~15s and ~$0.026 per document**. Projected for 40: **~11 minutes and ~$1–3.50**
for mapping, plus 3–4 minutes for accept. Prompt caching does the heavy lifting — the
~15k catalogue prefix bills at $0.50/M instead of $2.00/M after the first call, so cost
scales with *output* (how many requirements each document matches), not input.

Context is not a constraint: gpt-4.1 takes ~1M input tokens against a largest current
document of 2,485.

### The three fixes

**1. Per-document isolation.** `start_run` had one `try` around the whole loop, so the
first failure abandoned every remaining document. At ~80 API calls a 1% per-call
failure rate means P(all succeed) ≈ 45% — the run would be lost more often than not.
The `try` now wraps one document; a failure skips that document and continues.

**2. Rollback instead of committing partial work.** The old handler did
`run.status = "failed"; db.commit()`, and since `record_mappings` only calls `add()`,
that commit persisted every pending row. A run dying at document 25 left 25 documents'
evidence attached to a failed run — unusable, because `accept_run` refuses non-
`coverage_ready` runs, and actively misleading, because `latest_run_for_organization`
would find it.

**3. `clock_timestamp()` instead of `now()`.** PostgreSQL's `now()` returns the
*transaction* start time, so a 26.9-second run recorded `completed_at - started_at` as
**0.05s**. The field meant to answer "how long did this take" measured nothing.

### No fallback — the rule that shaped fix 1

A document that cannot be read produces **nothing**, and is recorded as **unread** —
never as "read and matched nothing". New `analysis_runs.skipped_documents` (JSONB:
document id, name, error) drives three consequences:

- `read_this_document()` returns False for a skipped document, so the per-document
  view cannot report `no_match` for something never looked at
- `coverage_report()` forces **`is_complete = false`** whenever anything was skipped —
  a skipped document makes coverage *unknowable*, not merely lower, so the gate can't
  wave through a run that never opened the risk register
- the gate modal shows skipped documents first, in error styling, above the missing
  requirements, stating that the counts below are incomplete by an unknown amount

Equally, a skip is **not** modelled by pretending its requirements are uncovered — that
would be the same fallback in reverse. A test asserts both directions.

### A bug found in the fix itself

The first implementation still lost data. Documents are processed in name order, and
with the commit deferred to the end of the loop, `db.rollback()` for a *later* failure
discarded every *earlier* document's pending rows. A two-document run with the failure
on the second one produced **zero** stored mappings — one failed call still costing the
whole run, which is precisely what the fix existed to prevent.

Corrected by committing per document, so each is atomic on its own. Verified both
directions — failure on the first document and on the last — with the survivor's rows
intact each time, and pinned by a test asserting the commit precedes the rollback.

### Verified

```
processing order: ['AI Incident Management procedure', 'AI Policy document']
failing the FIRST one:
  status                       : coverage_ready      (not 'failed')
  documents read               : 1 of 2
  rows for the FAILED document : 0
  rows from the SURVIVOR(S)    : 2
  read_this_document(skipped)  : False
  is_complete                  : False

failing the LAST one:
  rows for the FAILED document : 0
  rows from the SURVIVOR(S)    : 2      (the earlier document was NOT lost)
```

**93 tests pass** (9 run-resilience). Migration head `a6b7c8d9e0f1`.

### Before running 40 — two operational checks

1. **All 40 must be in one organization and tagged for the standard.**
   `list_current_documents` filters on both; documents spread across organizations will
   not run together.
2. **Check the Azure deployment's TPM quota.** 80 calls averaging ~8.8k tokens over
   ~11 minutes is roughly **64k tokens/minute**. Below that, 429s become systematic
   rather than transient, and the SDK's two retries won't absorb them — though with
   per-document isolation the run now survives and reports which documents were hit.

Do not run under `--reload`: a file save mid-run restarts the server and kills ~11
minutes of paid work.
