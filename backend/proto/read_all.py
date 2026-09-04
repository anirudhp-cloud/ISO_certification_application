# Extracts and profiles every document in the audit folder.
#
# Uses the application's own extractor, so what is profiled here is exactly what the
# LLM would receive — including its handling of tables, headers and reading order.
# The profile is mechanical: what the document IS, how it is structured, and the
# signals that decide whether it can satisfy a requirement at all (does it contain
# records or only a procedure; does it point at artefacts that were never submitted).

import json
import pathlib
import re
import sys

sys.path.insert(0, ".")

from app.extraction.document_extraction import extract_text

SRC = pathlib.Path("C:/Users/Admin/Documents/3.Documents-20260825T114856Z-1-001/3.Documents")
OUT = pathlib.Path("proto/doc_profiles.json")

# Wording that distinguishes a defined intention from evidence that something happened.
FUTURE = re.compile(r"\bshall\b|\bwill be\b|\bmust be\b|\bis to be\b", re.I)
PAST = re.compile(r"\bwas\b|\bwere\b|\bhas been\b|\bhave been\b|\bcompleted on\b|"
                  r"\bconducted on\b|\bapproved on\b|\bdated\b", re.I)
# A pointer to another artefact.
REF = re.compile(r"\b(?:refer(?:\s+to)?|as\s+per|see|maintained\s+in|recorded\s+in|"
                 r"documented\s+in|tracked\s+in)\s+"
                 r"((?:the\s+)?[A-Z][\w&/\- ]{3,58}?"
                 r"(?:Procedure|Policy|Register|Tracker|Matrix|Manual|Plan|Log|Checklist|"
                 r"Framework|Report|Record|Form|Statement))", re.I)
# Dated or numbered entries — the signature of an actual record rather than a template.
DATE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+"
                  r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})", re.I)
CONTROL_BLOCK = re.compile(r"document\s*(?:id|control|no)|version|classification|"
                           r"prepared\s*by|reviewed\s*by|approved\s*by", re.I)


def headings(text: str) -> list[str]:
    """Numbered section headings, which is how these documents are organised."""
    found = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^(\d{1,2}(?:\.\d{1,2})*)\.?\s+([A-Z][A-Za-z /&,'()-]{3,60})$", line)
        if m:
            found.append(f"{m.group(1)} {m.group(2)}")
    return found


def profile(path: pathlib.Path) -> dict:
    content = path.read_bytes()
    method, text, chunks = extract_text(path.name, content)
    words = len(text.split())
    return {
        "file": str(path.relative_to(SRC)).replace("\\", "/"),
        "ext": path.suffix.lower().lstrip("."),
        "kb": round(len(content) / 1024, 1),
        "method": method,
        "chunks": len(chunks or []),
        "chars": len(text),
        "words": words,
        "headings": headings(text)[:24],
        "heading_count": len(headings(text)),
        "shall_count": len(re.findall(r"\bshall\b", text, re.I)),
        "future_phrases": len(FUTURE.findall(text)),
        "past_phrases": len(PAST.findall(text)),
        "dates": sorted(set(DATE.findall(text)))[:8],
        "date_count": len(DATE.findall(text)),
        "has_control_block": bool(CONTROL_BLOCK.search(text[:2500])),
        "references": sorted({" ".join(m.split()).strip(" .,;") for m in REF.findall(text)}),
        "tables": text.count(" | "),
        "first_600": text[:600],
    }


if __name__ == "__main__":
    files = [p for p in sorted(SRC.rglob("*"))
             if p.is_file() and not p.name.startswith("~$")
             and p.suffix.lower() in {".docx", ".pptx", ".xlsx", ".pdf", ".txt"}]
    profiles = []
    for path in files:
        try:
            profiles.append(profile(path))
            print(f"  ok    {profiles[-1]['chars']:>7,} chars  {profiles[-1]['file'][:70]}", flush=True)
        except Exception as exc:
            print(f"  FAIL  {path.name}: {type(exc).__name__}: {exc}"[:150], flush=True)
            profiles.append({"file": str(path.relative_to(SRC)), "error": f"{type(exc).__name__}: {exc}"})
    OUT.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = [p for p in profiles if "error" not in p]
    print(f"\n{len(ok)} of {len(files)} extracted, {sum(p['chars'] for p in ok):,} chars total -> {OUT}")
