# Renders the judgement rules as a review document.
#
# A markdown file rather than code, because the acceptance tests are judgement calls
# about where a bar sits and need to be checked by someone who owns the standard
# before anything is built on them. Once validated, the same JSON drives the prompt.
#
# Each clause carries its Annex A / Annex B mapping, taken from pointers written in
# the standard's own text (extracted from the transcription in iso_text/). Only 5 of
# the 32 clauses point at specific controls; 24 have no annex link at all. Anyone who
# publishes a complete clause-to-control mapping table for ISO 42001 has invented it —
# controls attach to RISKS via 6.1.3, not to clauses.

import json
import pathlib

RULES = pathlib.Path("proto/rules_draft.json")
SEED = pathlib.Path("../seed_data/iso42001_requirements.json")
OUT = pathlib.Path("../ISO42001_judgement_rules.md")

# Pointers as the standard writes them. "Table A.1" is the table's name, not control
# A.1, and is excluded.
POINTERS = {
    "5.2":   {"controls": ["A.2"], "guidance": ["B.2"],
              "quote": "Control objectives and controls for establishing an AI policy are provided "
                       "in A.2 in Table A.1. Implementation guidance for these controls is "
                       "provided in B.2."},
    "5.3":   {"controls": ["A.3.2"], "guidance": ["B.3.2"],
              "quote": "NOTE A control for defining and allocating roles and responsibilities is "
                       "provided in A.3.2 in Table A.1. Implementation guidance for this control "
                       "is provided in B.3.2."},
    "6.1.3": {"controls": ["*"], "guidance": ["*"],
              "quote": "determine all controls that are necessary ... and compare the controls "
                       "with those in Annex A to verify that no necessary controls have been "
                       "omitted ... consider the guidance in Annex B"},
    "6.1.4": {"controls": ["A.5"], "guidance": [],
              "quote": "A.5 in Table A.1 provides controls for assessing impacts of AI systems."},
    "6.2":   {"controls": ["A.6.1", "A.9.3"], "guidance": ["B.6.1", "B.9.3"],
              "quote": "Control objectives and controls for identifying objectives for responsible "
                       "development and use of AI systems and measures to achieve them are "
                       "provided in A.6.1 and A.9.3 in Table A.1. Implementation guidance for "
                       "these controls is provided in B.6.1 and B.9.3."},
    "7.1":   {"controls": ["A.4"], "guidance": ["B.4"],
              "quote": "NOTE Control objectives and controls for AI resources are provided in A.4 "
                       "in Table A.1. Implementation guidance for these controls is provided in "
                       "Clause B.4."},
    "7.2":   {"controls": [], "guidance": ["B.4.6"],
              "quote": "NOTE 1 Implementation guidance for human resources including consideration "
                       "of necessary expertise is provided in B.4.6."},
    "8.1":   {"controls": ["*"], "guidance": ["*"],
              "quote": "The organization shall implement the controls determined according to "
                       "6.1.3 ... Annex A lists reference controls and Annex B provides "
                       "implementation guidance for them."},
}

FORM_MEANING = {
    "determination": "the organisation has worked the thing out and can show it",
    "process": "a defined, repeatable way of doing it exists",
    "documented_information": "it exists as a document, available for use",
    "record": "evidence that it actually happened, at least once",
}


def main() -> None:
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    seed = json.loads(SEED.read_text(encoding="utf-8"))["requirements"]
    controls = [r for r in seed if r["requirement_type"] == "control"]
    guidance_count = {r["code"]: len(r.get("implementation_guidance") or []) for r in controls}
    clause_order = [r["code"] for r in seed if r["requirement_type"] == "clause"]

    def expand(pointers: list[str]) -> list[str]:
        if pointers == ["*"]:
            return ["*"]
        out = []
        for p in pointers:
            out += [c["code"] for c in controls
                    if c["code"] == p or c["code"].startswith(p + ".")]
        return out

    total_reqs = sum(len(rules.get(c, {}).get("requirements", [])) for c in clause_order)
    mapped = {c for code in POINTERS for c in expand(POINTERS[code]["controls"]) if c != "*"}

    md: list[str] = []
    w = md.append

    w("# ISO/IEC 42001 — Judgement Rules")
    w("")
    w("The acceptance test for every requirement in clauses 4–10, with each clause's")
    w("Annex A / Annex B mapping. **This is a review document.** The tests are judgement")
    w("calls about where a bar sits; nothing should be built on them until they are checked.")
    w("")
    w("## How to read a requirement")
    w("")
    w("| Field | What it does |")
    w("|---|---|")
    w("| **subject** | what a passage must be *about*. A statement about a different artefact is inadmissible however well the wording fits — this is the test that stops a sentence about the *IMS Policy* satisfying an *AI policy* requirement. |")
    w("| **actor** | `organization` or `top_management`, exactly as the clause names it. Where it is top management, evidence must show an act — an approval, a signature, a minuted decision — not a document's claim that they are committed. |")
    w("| **form** | what kind of artefact satisfies it. A procedure saying reviews happen annually is not evidence that a review happened. |")
    w("| **met_when** | what a passage must actually say. |")
    w("| **partial_when** | the *only* route to a partial verdict. If evidence does not fit this description, the verdict is met or unmet — never a hedge for uncertainty. |")
    w("| **unmet_when** | near-misses that must not be credited, named so they can be refused. |")
    w("| **look for** | informative search aids from the clause's NOTES. NOTEs are informative in ISO, so these carry no verdict and can never make a requirement unmet. |")
    w("")
    w("Forms: " + " · ".join(f"**{k}** — {v}" for k, v in FORM_MEANING.items()))
    w("")

    w("## Totals")
    w("")
    w("```")
    w(f"clauses 4-10        {len(clause_order)} subclauses")
    w(f"requirements        {total_reqs} across those clauses")
    w(f"Annex A             {len(controls)} controls")
    w(f"Annex B             {sum(guidance_count.values())} guidance points")
    w("```")
    w("")

    w("## Clause → Annex A / Annex B")
    w("")
    w("Taken from pointers written in the standard's own text. **24 of 32 clauses have no")
    w("annex link at all** — including every clause in 4, 9 and 10. Only 5 point at specific")
    w("controls. The remaining 22 controls are reachable only through 6.1.3, from the risk")
    w("assessment: controls attach to **risks**, not to clauses.")
    w("")
    w("| Clause | Title | Annex A controls | Annex B points |")
    w("|---|---|---|---|")
    for code in clause_order:
        entry = rules.get(code, {})
        title = entry.get("title", "")
        ptr = POINTERS.get(code)
        if not ptr:
            w(f"| {code} | {title} | — | — |")
            continue
        codes = expand(ptr["controls"])
        if codes == ["*"]:
            w(f"| **{code}** | {title} | *all of Annex A — selection / implementation rule* | — |")
        elif not codes and ptr["guidance"]:
            w(f"| **{code}** | {title} | *none — guidance {', '.join(ptr['guidance'])} only* | — |")
        else:
            pts = sum(guidance_count.get(c, 0) for c in codes)
            w(f"| **{code}** | {title} | {', '.join(codes)} | {pts} |")
    w("")
    w(f"Controls reachable from a clause pointer: **{len(mapped)} of {len(controls)}**. "
      f"The other **{len(controls) - len(mapped)}** — A.7 data, A.8 information for interested "
      "parties, A.10 third-party relationships, most of A.6.2 life cycle — are reachable only "
      "via 6.1.3.")
    w("")
    w("### The pointers, quoted")
    w("")
    for code, ptr in POINTERS.items():
        w(f"**{code}** — *\"{ptr['quote']}\"*")
        w("")

    w("## Assessment units")
    w("")
    w("The mapping above gives the grouping. A unit is assessed in one call; its layers are")
    w("graded separately, because the consequence of failing each differs:")
    w("")
    w("```")
    w("clause requirement unmet    -> nonconformity. Clauses cannot be excluded.")
    w("control requirement unmet   -> nonconformity ONLY if the control is applicable")
    w("                               per the Statement of Applicability.")
    w("Annex B point unaddressed   -> opportunity for improvement. NEVER a nonconformity,")
    w("                               because every verb in Annex B is 'should'.")
    w("```")
    w("")
    merged = [c for c in POINTERS if expand(POINTERS[c]["controls"]) not in (["*"], [])]
    w(f"- **{len(merged)} merged units** — clause + its controls + their Annex B: "
      f"{', '.join(merged)}")
    w(f"- **{len(clause_order) - len(merged)} clause-only units** — no annex layer, so every "
      "shortfall is a potential nonconformity with no OFI layer to soften it")
    w(f"- **{len(controls) - len(mapped)} control-only units** — controls with no clause "
      "pointer, plus their Annex B")
    w("")

    w("---")
    w("")
    w("# The rules, clause by clause")
    w("")
    for code in clause_order:
        entry = rules.get(code)
        if not entry:
            continue
        requirements = entry.get("requirements", [])
        ptr = POINTERS.get(code)
        w(f"## {code} — {entry['title']}")
        w("")
        if ptr:
            codes = expand(ptr["controls"])
            if codes == ["*"]:
                annex = "all of Annex A (selection / implementation rule)"
            elif codes:
                annex = ", ".join(codes)
            else:
                annex = f"none — guidance {', '.join(ptr['guidance'])} only"
        else:
            annex = "**none** — the standard gives this clause no Annex A control and no Annex B guidance"
        w(f"*{len(requirements)} requirements · Annex A: {annex}*")
        w("")
        for index, r in enumerate(requirements):
            w(f"### `{code}/{index}` {r.get('text','')}")
            w("")
            w(f"- **subject** — {r.get('subject','')}")
            w(f"- **actor** — `{r.get('actor','')}` · **form** — `{r.get('form','')}`")
            w(f"- **met when** — {r.get('met_when','')}")
            w(f"- **partial when** — {r.get('partial_when','')}")
            w(f"- **unmet when** — {r.get('unmet_when','')}")
            if r.get("contradiction_watch"):
                w(f"- **contradiction watch** — {r['contradiction_watch']}")
            if r.get("look_for"):
                w("- **look for** *(informative, from the standard's NOTES — no verdict of their own)*")
                for aid in r["look_for"]:
                    w(f"  - {aid}")
            w("")
        w("")

    OUT.write_text("\n".join(md), encoding="utf-8")
    print(f"written: {OUT.resolve()}")
    print(f"  {len(clause_order)} clauses, {total_reqs} requirements, {len(md):,} lines")


if __name__ == "__main__":
    main()
