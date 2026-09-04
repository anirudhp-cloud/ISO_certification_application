# Assembles the complete clause 4.1 prompt, runs it against a real document, and
# writes the whole trace — prompt, document, raw model output, counted result — to a
# file that can be read end to end.

import json
import pathlib
import re
import sys

sys.path.insert(0, ".")

from app.ai.openai_client import _client
from app.config import settings
from derive41_v2 import CLAUSE_41, render
from prompt_library.prompt_v4_draft import SYSTEM_PROMPT, VERSION

LOG = pathlib.Path(
    "../prompt_logs/20260904_122847_976953__map_clause__2A.AI_Policy_for_TechVest.txt"
)
OUT = pathlib.Path("../ISO42001_clause_4.1_prompt_and_output.txt")


def document_text() -> str:
    raw = LOG.read_text(encoding="utf-8", errors="replace")
    body = raw.split("USER MESSAGE (role: user)", 1)[1]
    return "\n".join(re.sub(r"^\s*\d+\|", "", line) for line in body.splitlines()).strip()


system = SYSTEM_PROMPT + "\n\n" + render(CLAUSE_41)
text = document_text()

response = _client.chat.completions.create(
    model=settings.llm_deployment,
    response_format={"type": "json_object"},
    temperature=0,
    seed=settings.llm_seed,
    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ],
)
raw = response.choices[0].message.content
result = json.loads(raw)

met = sum(1 for v in result["requirements"] if v["verdict"] == "met")
partial = sum(1 for v in result["requirements"] if v["verdict"] == "partial")
total = len(CLAUSE_41["requirements"])

parts = [
    "=" * 78,
    f"CLAUSE 4.1 — THE COMPLETE PROMPT AND OUTPUT   (prompt {VERSION})",
    "=" * 78,
    "",
    "One API call. system message = everything in PART 1 below. user message = the",
    f"document's full extracted text. temperature=0, seed={settings.llm_seed},",
    "response_format=json_object.",
    "",
    "",
    "#" * 78,
    "# PART 1 — THE SYSTEM MESSAGE (what the model is told)",
    "#" * 78,
    "",
    system,
    "",
    "",
    "#" * 78,
    "# PART 2 — THE USER MESSAGE (the document being assessed)",
    "#" * 78,
    "",
    f"Document: 2A.AI_Policy for TechVest — {len(text):,} characters.",
    "First 1,500 characters, to show what the model is reading:",
    "",
    text[:1500],
    "",
    "        [... remainder of the document ...]",
    "",
    "",
    "#" * 78,
    "# PART 3 — THE RAW MODEL OUTPUT",
    "#" * 78,
    "",
    raw,
    "",
    "",
    "#" * 78,
    "# PART 4 — WHAT THE APPLICATION DOES WITH IT",
    "#" * 78,
    "",
]

for verdict in result["requirements"]:
    item = CLAUSE_41["requirements"][verdict["index"]]
    parts += [
        f"[{verdict['index']}] {verdict['verdict'].upper()}",
        f"     requirement: {item['text']}",
        f"     actor: {item['actor']}   satisfied by: {item['evidence_kind']}",
    ]
    quote = verdict.get("quote")
    if quote:
        parts.append(f"     quote:      {quote[:300]!r}")
        parts.append("     -> located in the PDF by verbatim search, highlighted amber,")
        parts.append("        opened at that page when the auditor clicks the citation")
    else:
        parts.append("     quote:      none — nothing in this document addresses it")
        parts.append("     -> rendered as 'Nothing in this document addresses this.'")
        parts.append("        No highlight: an absence has no passage to point at")
    parts.append("")

parts += [
    "COUNTED IN CODE (the model returns no score):",
    f"  met     = {met}",
    f"  partial = {partial}   (counts as NOT satisfied — partly documented is not documented)",
    f"  unmet   = {total - met - partial}",
    f"  fraction shown to the auditor = '{met} of {total} requirements satisfied'",
    "",
    f"tokens: {response.usage.prompt_tokens} in / {response.usage.completion_tokens} out",
]

OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"written: {OUT.resolve()}  ({OUT.stat().st_size:,} bytes)")
print()
for verdict in result["requirements"]:
    o = CLAUSE_41["requirements"][verdict["index"]]
    q = (verdict.get("quote") or "").replace("\n", " ")
    print(f"[{verdict['index']}] {verdict['verdict'].upper():8} {o['text'][:58]}")
    print(f"    {q[:120]!r}" if q else "    (no quote)")
print()
print(f"counted: {met} of {total}   (partial={partial})")
print(f"tokens: {response.usage.prompt_tokens} in / {response.usage.completion_tokens} out")
