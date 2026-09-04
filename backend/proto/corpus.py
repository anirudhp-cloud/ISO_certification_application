# Rebuilds the document corpus from prompt_logs.
#
# Its own module because run_proto.py runs its assessment at import time, so importing
# a helper from there fired a real API call as a side effect — which is how the ceiling
# probe ended up repeating the very request it was meant to measure.

import pathlib
import re

LOGS = pathlib.Path("../prompt_logs")


def load_corpus() -> list[tuple[str, str]]:
    """(display name, extracted text) per document, newest dump per name.

    The database was wiped, but each analysis call dumped its user message, so the
    text here is the same bytes the real run assessed.
    """
    by_name: dict[str, tuple[str, str]] = {}
    for f in sorted(LOGS.glob("*20260904*map_clause*.txt")):
        name = f.stem.split("__map_clause__")[-1]
        if name.startswith("demo"):
            continue
        raw = f.read_text(encoding="utf-8", errors="replace")
        if "USER MESSAGE" not in raw:
            continue
        body = raw.split("USER MESSAGE", 1)[1]
        text = "\n".join(re.sub(r"^\s*\d+\|", "", line) for line in body.splitlines()).strip()
        if len(text) > 200:
            by_name[name] = (name.replace("_", " "), text)
    return list(by_name.values())
