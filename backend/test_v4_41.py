# Runs the v4 draft prompt for clause 4.1 against a real document, and prints the
# assembled prompt so it can be read as the model receives it.
#
# The document text comes from prompt_logs — the database was wiped, and a dump of a
# real analysis call still holds the extracted text, so the comparison is against the
# same bytes the v3 run saw.

import json
import pathlib
import re
import sys

sys.path.insert(0, ".")

from app.ai.openai_client import _client
from app.config import settings
from derive45 import DERIVED
from prompt_library.prompt_v4_draft import SYSTEM_PROMPT, VERSION, render_requirement

CODE = "4.1"
LOG = pathlib.Path("../prompt_logs/20260904_122847_976953__map_clause__2A.AI_Policy_for_TechVest.txt")


def document_text() -> str:
    raw = LOG.read_text(encoding="utf-8", errors="replace")
    body = raw.split("USER MESSAGE (role: user)", 1)[1]
    # The dump numbers each line for readability; strip the numbering back off.
    return "\n".join(re.sub(r"^\s*\d+\|", "", line) for line in body.splitlines()).strip()


entry = DERIVED[CODE]
system = SYSTEM_PROMPT + "\n\n" + render_requirement(CODE, entry["title"], entry)

print("=" * 78)
print("THE REQUIREMENT BLOCK, AS THE MODEL RECEIVES IT")
print("=" * 78)
print(render_requirement(CODE, entry["title"], entry))
print()
print(f"full system prompt: {len(system):,} chars   (v3 clause prompt was 30,484 for all 32)")

text = document_text()
print(f"document: 2A.AI_Policy for TechVest, {len(text):,} chars")
print()

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
result = json.loads(response.choices[0].message.content)

print("=" * 78)
print(f"RESULT — prompt {VERSION}")
print("=" * 78)
for verdict in result["obligations"]:
    index = verdict["index"]
    obligation = entry["obligations"][index]
    print(f"[{index}] {verdict['verdict'].upper():8} {obligation['text'][:64]}")
    print(f"    actor {obligation['actor']}, satisfied by {obligation['evidence_kind']}")
    quote = (verdict.get("quote") or "").replace("\n", " ")
    print(f"    {quote[:150]!r}" if quote else "    (no quote — nothing addresses this)")
met = sum(1 for v in result["obligations"] if v["verdict"] == "met")
print()
print(f"counted in code: {met} of {len(entry['obligations'])} obligations satisfied")
print(f"usage: {response.usage.prompt_tokens} in / {response.usage.completion_tokens} out")
