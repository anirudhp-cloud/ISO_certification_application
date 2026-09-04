# Runs the v5 prototype: one call, whole corpus, the AI policy unit.
#
# Writes the complete trace (prompt structure, raw output, counted result) to a file,
# and prints a readable summary. The corpus is rebuilt from prompt_logs because the
# database was wiped — a dump of a real analysis call still holds each document's
# extracted text, so this runs against the same bytes the v3 run saw.

import json
import pathlib
import re
import sys

sys.path.insert(0, ".")

from app.ai.openai_client import _client
from app.config import settings
from proto.corpus import load_corpus
from proto.prompt_v5 import VERSION, build_system
from proto.unit_ai_policy import UNIT, render_unit

LOGS = pathlib.Path("../prompt_logs")
OUT = pathlib.Path("../ISO42001_prototype_ai_policy.txt")




def all_requirements(unit: dict) -> dict:
    items = {r["id"]: dict(r, layer="clause", source=unit["clause"]["code"])
             for r in unit["clause"]["requirements"]}
    for control in unit["controls"]:
        for r in control["requirements"]:
            items[r["id"]] = dict(r, layer="control", source=control["code"])
    return items


corpus = load_corpus()
MAX_DOCS = int(__import__("os").environ.get("PROTO_MAX_DOCS", "20"))
if len(corpus) > MAX_DOCS:
    print(f"corpus trimmed to {MAX_DOCS} of {len(corpus)} documents to fit the "
          f"deployment's per-call ceiling (~40k tokens OK, ~55k refused)")
    corpus = corpus[:MAX_DOCS]
system = build_system(corpus)
user = render_unit(UNIT)
items = all_requirements(UNIT)

print(f"corpus: {len(corpus)} documents, {len(system):,} chars in the system message")
print(f"unit:   {len(user):,} chars, {len(items)} requirements, {len(UNIT['guidance'])} guidance points")
print("calling…")

def call(attempt=0):
    # A whole-corpus call is ~58k tokens, which is large enough to bounce off the
    # deployment's tokens-per-minute quota. Worth recording: at 54 units per run this
    # pacing is a real constraint on the design, not just a test-script annoyance.
    import time
    try:
        return _client.chat.completions.create(
            model=settings.llm_deployment,
            response_format={"type": "json_object"},
            temperature=0,
            seed=settings.llm_seed,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
    except Exception as exc:
        if attempt >= 6:
            raise
        wait = 20 * (attempt + 1)
        print(f"  {type(exc).__name__}; waiting {wait}s and retrying", flush=True)
        time.sleep(wait)
        return call(attempt + 1)


response = call()
raw = response.choices[0].message.content
result = json.loads(raw)

verdicts = {r["id"]: r for r in result.get("requirements", [])}
clause_ids = [r["id"] for r in UNIT["clause"]["requirements"]]
control_ids = [r["id"] for c in UNIT["controls"] for r in c["requirements"]]


def count(ids, value):
    return sum(1 for i in ids if verdicts.get(i, {}).get("verdict") == value)


lines = []


def emit(text=""):
    lines.append(text)
    print(text)


emit()
emit("=" * 78)
emit(f"LAYER 1 — CLAUSE 5.2 (mandatory, cannot be excluded)")
emit("=" * 78)
for rid in clause_ids:
    v = verdicts.get(rid, {"verdict": "MISSING"})
    item = items[rid]
    emit(f"{rid}  {v['verdict'].upper():13} {item['text'][:60]}")
    for ev in v.get("evidence", []) or []:
        chain = " -> ".join(ev.get("reference_chain") or [])
        tag = f"[{ev.get('kind', 'direct')}{': ' + chain if chain else ''}]"
        emit(f"        {tag} {ev.get('document', '?')}")
        emit(f"          {(ev.get('quote') or '')[:118]!r}")
    if v.get("contradicted_by"):
        c = v["contradicted_by"]
        emit(f"        CONTRADICTED BY {c.get('document')}: {(c.get('quote') or '')[:96]!r}")
    if v.get("shortfall"):
        emit(f"        shortfall: {v['shortfall'][:110]}")
    if v.get("recommendation"):
        emit(f"        recommend: {v['recommendation'][:110]}")

emit()
emit("=" * 78)
emit("LAYER 2 — ANNEX A CONTROLS (excludable via the Statement of Applicability)")
emit("=" * 78)
for rid in control_ids:
    v = verdicts.get(rid, {"verdict": "MISSING"})
    emit(f"{rid}  {v['verdict'].upper():13} {items[rid]['text'][:58]}")
    for ev in v.get("evidence", []) or []:
        emit(f"        [{ev.get('kind', 'direct')}] {ev.get('document', '?')}: {(ev.get('quote') or '')[:96]!r}")
    if v.get("shortfall"):
        emit(f"        shortfall: {v['shortfall'][:110]}")
    if v.get("recommendation"):
        emit(f"        recommend: {v['recommendation'][:110]}")

guidance = result.get("guidance", []) or []
addressed = [g for g in guidance if g.get("addressed")]
emit()
emit("=" * 78)
emit(f"LAYER 3 — ANNEX B GUIDANCE: {len(addressed)} of {len(UNIT['guidance'])} addressed")
emit("(informative — unaddressed points are OFIs, never nonconformities)")
emit("=" * 78)
for g in guidance:
    mark = "addressed " if g.get("addressed") else "NOT       "
    idx = g.get("id", "?")
    try:
        point = UNIT["guidance"][int(str(idx).lstrip("G"))][1]
    except (ValueError, IndexError):
        point = "?"
    emit(f"  {idx} {mark} {point[:88]}")

unresolved = result.get("unresolved_references", []) or []
emit()
emit("=" * 78)
emit(f"CITED BUT NEVER SUBMITTED — {len(unresolved)} reference(s)")
emit("=" * 78)
for u in unresolved:
    emit(f"  {u.get('document', '?')} -> {u.get('refers_to', '?')}")
    if u.get("quote"):
        emit(f"      {u['quote'][:110]!r}")

emit()
emit("=" * 78)
emit("COUNTED IN CODE (the model returned no score)")
emit("=" * 78)
emit(f"  clause 5.2      {count(clause_ids, 'met')} of {len(clause_ids)} met"
     f"   (partial {count(clause_ids, 'partial')},"
     f" unmet {count(clause_ids, 'unmet')},"
     f" contradicted {count(clause_ids, 'contradicted')})")
emit(f"  Annex A         {count(control_ids, 'met')} of {len(control_ids)} met"
     f"   (partial {count(control_ids, 'partial')},"
     f" unmet {count(control_ids, 'unmet')},"
     f" contradicted {count(control_ids, 'contradicted')})")
emit(f"  Annex B         {len(addressed)} of {len(UNIT['guidance'])} addressed -> "
     f"{len(UNIT['guidance']) - len(addressed)} OFI(s)")
emit()
emit(f"tokens: {response.usage.prompt_tokens:,} in / {response.usage.completion_tokens:,} out")
cached = getattr(getattr(response.usage, "prompt_tokens_details", None), "cached_tokens", 0) or 0
emit(f"cached: {cached:,} of the input")
cost = (response.usage.prompt_tokens - cached) * 2 / 1e6 + cached * 0.5 / 1e6 \
       + response.usage.completion_tokens * 8 / 1e6
emit(f"cost:   ${cost:.3f} for this one call; x54 units ~= ${cost * 54:.2f} per run "
     f"(the corpus is cached after the first call)")

OUT.write_text(
    "\n".join([
        "=" * 78,
        f"PROTOTYPE — REQUIREMENT-FIRST ASSESSMENT   (prompt {VERSION})",
        "=" * 78,
        "",
        f"ONE API call. system message = instructions + all {len(corpus)} documents",
        "(the static, cacheable prefix). user message = the assessment unit below.",
        f"temperature=0, seed={settings.llm_seed}, response_format=json_object.",
        "",
        "#" * 78,
        "# PART 1 — SYSTEM MESSAGE, INSTRUCTIONS",
        "#" * 78,
        "",
        system.split("=" * 74)[0],
        "",
        "#" * 78,
        f"# PART 2 — SYSTEM MESSAGE, THE CORPUS ({len(corpus)} documents, {len(system):,} chars)",
        "#" * 78,
        "",
        "\n".join(f"  DOCUMENT: {name}   ({len(text):,} chars)" for name, text in corpus),
        "",
        "        [each document's full text follows its header in the real prompt]",
        "",
        "#" * 78,
        "# PART 3 — USER MESSAGE, THE ASSESSMENT UNIT",
        "#" * 78,
        "",
        user,
        "",
        "#" * 78,
        "# PART 4 — RAW MODEL OUTPUT",
        "#" * 78,
        "",
        raw,
        "",
        "#" * 78,
        "# PART 5 — WHAT THE APPLICATION MAKES OF IT",
        "#" * 78,
        "",
        "\n".join(lines),
    ]),
    encoding="utf-8",
)
print()
print(f"full trace written: {OUT.resolve()}  ({OUT.stat().st_size:,} bytes)")
