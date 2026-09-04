# Runs the v6 prototype (judgement rules in the prompt) on one unit, and validates the
# output in code rather than trusting the labels.
#
# Three checks the code makes, because v5 showed the model will assert a verdict the
# evidence does not support:
#   - verdict vs matched: a "partial" whose matched test is not "partial_when" is
#     self-inconsistent, and is reported as such.
#   - duplicate quotes: rule 6 says one quote supports one requirement. Asking was not
#     enough in v5 — the same IMS Policy sentence was used for two requirements — so
#     duplicates are detected here.
#   - contradiction_checked: every "met" must carry it. A "met" without the sweep is
#     an unchecked assertion.

import json
import os
import pathlib
import sys
import time

sys.path.insert(0, ".")

from app.ai.openai_client import _client
from app.config import settings
from proto.corpus import load_corpus
from proto.prompt_v6 import VERSION, build_system, render_unit
from proto.rules import AI_POLICY, CLAUSE_4_1
from proto.unit_ai_policy import UNIT as POLICY_UNIT

UNITS = {"ai_policy": (AI_POLICY, POLICY_UNIT["guidance"]), "4.1": (CLAUSE_4_1, None)}
choice = sys.argv[1] if len(sys.argv) > 1 else "ai_policy"
unit, guidance = UNITS[choice]

MAX_DOCS = int(os.environ.get("PROTO_MAX_DOCS", "20"))
corpus = load_corpus()[:MAX_DOCS]
system = build_system(corpus)
user = render_unit(unit, guidance)
by_id = {r["id"]: r for r in unit["requirements"]}

print(f"unit:   {unit['unit']}  —  {len(by_id)} requirements, "
      f"{len(guidance or [])} Annex B points")
print(f"corpus: {len(corpus)} documents   system {len(system):,} chars   unit {len(user):,} chars")


def call(attempt=0):
    try:
        return _client.chat.completions.create(
            model=settings.llm_deployment, response_format={"type": "json_object"},
            temperature=0, seed=settings.llm_seed,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    except Exception as exc:
        if attempt >= 4:
            raise
        wait = 25 * (attempt + 1)
        print(f"  {type(exc).__name__}; waiting {wait}s", flush=True)
        time.sleep(wait)
        return call(attempt + 1)


response = call()
raw = response.choices[0].message.content
result = json.loads(raw)

MARK = {"met": "MET", "partial": "PARTIAL", "unmet": "UNMET", "contradicted": "CONTRADICTED"}
lines = []


def emit(text=""):
    lines.append(text)
    print(text)


emit()
emit("=" * 78)
emit(f"{unit['title'].upper()} — verdicts   (prompt {VERSION})")
emit("=" * 78)

seen_quotes: dict[str, str] = {}
problems = []
for entry in result.get("requirements", []):
    rid = entry.get("id")
    spec = by_id.get(rid)
    if spec is None:
        problems.append(f"{rid}: not a requirement of this unit")
        continue
    verdict = entry.get("verdict", "?")
    layer = "control" if rid.startswith("A.") else "clause"
    emit(f"\n{rid:9} [{layer}]  {MARK.get(verdict, verdict)}"
         f"   (matched: {entry.get('matched', '—')})")
    emit(f"          {spec['text'][:88]}")
    for ev in entry.get("evidence") or []:
        chain = " -> ".join(ev.get("reference_chain") or [])
        emit(f"    {ev.get('kind', 'direct')}{' via ' + chain if chain else ''}"
             f" | {ev.get('document', '?')}")
        quote = (ev.get("quote") or "").replace("\n", " ")
        emit(f"      {quote[:120]!r}")
        if quote and quote[:80] in seen_quotes:
            problems.append(f"{rid}: reuses the quote already used for {seen_quotes[quote[:80]]}")
        elif quote:
            seen_quotes[quote[:80]] = rid
    if entry.get("contradicted_by"):
        c = entry["contradicted_by"]
        emit(f"    CONTRADICTED BY | {c.get('document')}")
        emit(f"      {(c.get('quote') or '').replace(chr(10), ' ')[:120]!r}")
    if entry.get("shortfall"):
        emit(f"    shortfall: {entry['shortfall'][:130]}")
    if entry.get("recommendation"):
        emit(f"    recommend: {entry['recommendation'][:130]}")

    expected = {"met": "met_when", "partial": "partial_when", "unmet": "unmet_when",
                "contradicted": "met_when"}
    if entry.get("matched") and entry["matched"] != expected.get(verdict):
        problems.append(f"{rid}: verdict '{verdict}' but matched '{entry['matched']}'")
    if verdict == "met" and not entry.get("contradiction_checked"):
        problems.append(f"{rid}: 'met' without the contradiction sweep")

missing = [rid for rid in by_id if rid not in {e.get("id") for e in result.get("requirements", [])}]
if missing:
    problems.append(f"no verdict returned for: {', '.join(missing)}")

guide = result.get("guidance") or []
addressed = [g for g in guide if g.get("addressed")]
if guidance:
    emit()
    emit("=" * 78)
    emit(f"ANNEX B — {len(addressed)} of {len(guidance)} addressed  "
         f"({len(guidance) - len(addressed)} OFI)")
    emit("=" * 78)
    for g in guide:
        if not g.get("addressed"):
            try:
                point = guidance[int(str(g.get("id", "G99")).lstrip("G"))][1]
            except (ValueError, IndexError):
                point = "?"
            emit(f"  NOT ADDRESSED  {g.get('id')}  {point[:92]}")

unresolved = result.get("unresolved_references") or []
emit()
emit("=" * 78)
emit(f"CITED BUT NEVER SUBMITTED — {len(unresolved)}")
emit("=" * 78)
for u in unresolved:
    emit(f"  {u.get('document', '?')}  ->  {u.get('refers_to', '?')}")

clause_ids = [r for r in by_id if not r.startswith("A.")]
control_ids = [r for r in by_id if r.startswith("A.")]
verdicts = {e.get("id"): e.get("verdict") for e in result.get("requirements", [])}


def tally(ids):
    return {v: sum(1 for i in ids if verdicts.get(i) == v)
            for v in ("met", "partial", "unmet", "contradicted")}


emit()
emit("=" * 78)
emit("COUNTED IN CODE")
emit("=" * 78)
if clause_ids:
    t = tally(clause_ids)
    emit(f"  clause  {t['met']} of {len(clause_ids)} met   "
         f"(partial {t['partial']}, unmet {t['unmet']}, contradicted {t['contradicted']})")
if control_ids:
    t = tally(control_ids)
    emit(f"  Annex A {t['met']} of {len(control_ids)} met   "
         f"(partial {t['partial']}, unmet {t['unmet']}, contradicted {t['contradicted']})")
if guidance:
    emit(f"  Annex B {len(addressed)} of {len(guidance)} addressed")

emit()
emit("=" * 78)
emit(f"SELF-CONSISTENCY CHECKS — {len(problems)} problem(s)")
emit("=" * 78)
for p in problems:
    emit(f"  {p}")
if not problems:
    emit("  none: every verdict agrees with its matched test, no quote is reused,")
    emit("  and every 'met' carries the contradiction sweep.")

emit()
emit(f"tokens {response.usage.prompt_tokens:,} in / {response.usage.completion_tokens:,} out")

out = pathlib.Path(f"../ISO42001_v6_{unit['unit']}.txt")
out.write_text("\n".join([
    "=" * 78, f"PROMPT STRUCTURE AND RESULT — {unit['title']}   ({VERSION})", "=" * 78, "",
    "ONE API call.",
    f"  system message = instructions + all {len(corpus)} documents (static, cacheable)",
    "  user message   = the assessment unit below",
    f"  temperature=0, seed={settings.llm_seed}, response_format=json_object",
    "", "#" * 78, "# PART 1 — SYSTEM MESSAGE: INSTRUCTIONS", "#" * 78, "",
    system.split("=" * 74)[0],
    "#" * 78, f"# PART 2 — SYSTEM MESSAGE: THE CORPUS ({len(corpus)} documents)", "#" * 78, "",
    "\n".join(f"  DOCUMENT: {n}   ({len(t):,} chars)" for n, t in corpus),
    "", "        [each document's full text follows its header in the real prompt]", "",
    "#" * 78, "# PART 3 — USER MESSAGE: THE ASSESSMENT UNIT", "#" * 78, "", user,
    "", "#" * 78, "# PART 4 — RAW MODEL OUTPUT", "#" * 78, "", raw,
    "", "#" * 78, "# PART 5 — VERDICTS AND CHECKS", "#" * 78, "", "\n".join(lines),
]), encoding="utf-8")
print(f"\nwritten: {out.resolve()}  ({out.stat().st_size:,} bytes)")
