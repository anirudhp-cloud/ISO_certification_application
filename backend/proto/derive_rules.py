# Derives the judgement rules for every clause from the transcribed standard text.
#
# The clause text in iso_text/ is authoritative — transcribed from the licensed PDF —
# so the requirements come from the printed "shall" wording rather than from a
# paraphrase. That was the original defect: the old catalogue was derived from my prose
# summary, which collapsed the nested lists the standard uses to state separate duties
# (clause 5.1 has 8 lettered commitments; the catalogue had 5).
#
# The acceptance tests (met_when / partial_when / unmet_when) are DRAFTED here and
# marked as drafts. They are judgement calls about where a bar sits, so they need
# review by someone who owns the standard — which is the point of emitting them as a
# document first. The two units already validated by hand and by a live run
# (clause 4.1, and the AI policy unit) are used as the worked examples in the prompt.

import json
import pathlib
import re
import sys
import time

sys.path.insert(0, ".")

from app.ai.openai_client import _client
from app.config import settings

OUT = pathlib.Path("proto/rules_draft.json")

INSTRUCTIONS = """You are decomposing one clause of ISO/IEC 42001:2023 into its individual
REQUIREMENTS, and writing the acceptance test for each, for use in a documentary
conformity assessment.

DECOMPOSITION — one requirement per separately-evidenceable printed duty:
  - every lettered or dashed item under a "shall" is its own requirement
  - a compound verb list inside one sentence splits ONLY where the evidence differs
    ("establish, implement and maintain" is one artefact set; "document the processes
    and their interactions" is a different artefact)
  - "shall retain documented information about X" is ALWAYS its own requirement,
    separate from the duty to have the process
  - NOTE content is never a requirement. NOTEs are informative in ISO. Put their
    content in look_for instead.

For each requirement give:
  text          the duty, in the standard's own terms, as a statement to be tested
  actor         "organization" or "top_management" — exactly as the clause names it
  form          "determination" (worked out and showable) | "process" (a defined
                repeatable way exists) | "documented_information" (exists as a
                document) | "record" (evidence it actually happened)
  subject       what a passage must be ABOUT to be admissible. Be specific: if the
                duty concerns the AI policy, a statement about a different policy is
                inadmissible however well the wording fits.
  met_when      what a passage must actually say. Concrete.
  partial_when  the ONLY route to a partial verdict. Describe genuinely incomplete
                evidence — part of what is required present, part absent; an intention
                rather than a practice.
  unmet_when    the near-misses that must NOT be credited. Name the plausible wrong
                answers: an adjacent topic, a responsibility instead of a
                determination, a procedure where a record is required, a
                cross-reference to an unseen artefact.
  look_for      informative search aids from this clause's NOTES, if any. [] if none.

Where a requirement is likely to be contradicted elsewhere in a document set, add
contradiction_watch describing where that conflict sits.

WORKED EXAMPLE of the intended depth, for clause 5.2's sixth requirement:
  text: "The AI policy is communicated within the organization"
  actor: "organization"
  form: "record"
  subject: "the AI policy - NOT any other policy"
  met_when: "a passage states how THIS AI POLICY is communicated internally
             (publication, induction, mandatory training, attestation), or evidences
             that it was"
  partial_when: "an intention to communicate is stated with no mechanism, or only
                 future amendments are said to be communicated"
  unmet_when: "nothing addresses communication of the AI policy. A statement about a
               DIFFERENT policy being communicated - the IMS Policy, the Quality
               Policy - is inadmissible"

Output strict JSON only:
{"requirements":[{"text":...,"actor":...,"form":...,"subject":...,"met_when":...,
"partial_when":...,"unmet_when":...,"look_for":[...],"contradiction_watch":...}]}
Omit contradiction_watch where it does not apply.
"""


def clause_segments() -> dict[str, str]:
    """Each clause's own text, cut out of the transcription by heading."""
    catalog = json.load(open("../seed_data/iso42001_requirements.json", encoding="utf-8"))
    codes = [r["code"] for r in catalog["requirements"] if r["requirement_type"] == "clause"]
    text = "\n".join(
        pathlib.Path(f"iso_text/page_{i:03d}.txt").read_text(encoding="utf-8")
        for i in range(13, 25) if pathlib.Path(f"iso_text/page_{i:03d}.txt").exists()
    )
    marks = []
    for code in sorted(codes, key=len, reverse=True):
        for m in re.finditer(rf"^[#*\s]*{re.escape(code)}\s+[A-Z]", text, re.M):
            marks.append((m.start(), code))
    marks.sort()
    segments = {}
    for i, (start, code) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        segments.setdefault(code, text[start:end].strip())
    return segments


def derive(code: str, title: str, body: str, attempt: int = 0) -> list[dict]:
    try:
        response = _client.chat.completions.create(
            model=settings.llm_deployment,
            response_format={"type": "json_object"},
            temperature=0,
            seed=settings.llm_seed,
            messages=[
                {"role": "system", "content": INSTRUCTIONS},
                {"role": "user", "content": f"CLAUSE {code} — {title}\n\n{body}"},
            ],
        )
        return json.loads(response.choices[0].message.content).get("requirements", [])
    except Exception as exc:
        if attempt >= 4:
            print(f"    FAILED {code}: {type(exc).__name__}", flush=True)
            return []
        time.sleep(20 * (attempt + 1))
        return derive(code, title, body, attempt + 1)


if __name__ == "__main__":
    catalog = json.load(open("../seed_data/iso42001_requirements.json", encoding="utf-8"))
    clauses = [r for r in catalog["requirements"] if r["requirement_type"] == "clause"]
    segments = clause_segments()
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

    for clause in clauses:
        code = clause["code"]
        if code in done and done[code].get("requirements"):
            print(f"  {code:7} cached ({len(done[code]['requirements'])})", flush=True)
            continue
        body = segments.get(code, "")
        if not body:
            print(f"  {code:7} NO TEXT FOUND — skipped", flush=True)
            continue
        requirements = derive(code, clause["title"], body)
        done[code] = {"title": clause["title"], "requirements": requirements}
        OUT.write_text(json.dumps(done, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {code:7} {len(requirements):2} requirements", flush=True)
        time.sleep(3)

    total = sum(len(v["requirements"]) for v in done.values())
    print(f"\n{len(done)} clauses, {total} requirements -> {OUT}")
