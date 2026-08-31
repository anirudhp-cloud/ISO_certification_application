# Deterministic source-citation lookup — given a finding's quoted rationale
# and the document's position-tagged extraction chunks (see
# app/extraction/document_extraction.py), finds exactly which chunk the quote
# came from and returns its location label (e.g. "Paragraph 12", "Page 3,
# Paragraph 2"). Never asks the LLM to self-report a position — it's already
# required to quote verbatim (see prompt_library/system_prompt_42k.py), and
# this just looks that quote up against the real document, in code.

import re


def _normalize(text: str) -> str:
    """Collapse whitespace so a quote that wrapped differently in the LLM's
    output still matches the source chunk's text."""
    return re.sub(r"\s+", " ", text).strip().lower()


def locate_quote(chunks: list[dict] | None, quote: str | None) -> str | None:
    if not chunks or not quote:
        return None

    normalized_quote = _normalize(quote)
    if not normalized_quote:
        return None

    # 1. Short quote sitting inside one chunk — the common case.
    for chunk in chunks:
        if normalized_quote in _normalize(chunk["text"]):
            return chunk["location"]

    # 2. Quote SPANNING several chunks. Models routinely quote a heading plus the
    #    paragraphs beneath it, while chunks are one paragraph or table row each, so
    #    no single chunk contains the whole thing. Measured on a real policy document,
    #    this was 9 of 17 citations failing — over half the feature — with every one
    #    of those quotes present in the document, just not in one chunk.
    #
    #    Cite where the quoted passage STARTS: the first chunk, in document order,
    #    whose text appears in the quote. Requiring a reasonable length avoids
    #    matching an incidental short line ("Contents") that happens to occur inside a
    #    long quote.
    for chunk in chunks:
        chunk_text = _normalize(chunk["text"])
        if len(chunk_text) >= 25 and chunk_text in normalized_quote:
            return chunk["location"]

    # 3. Transcription drift (extra leading/trailing words) — try the longest ~half
    #    of the quote before giving up.
    words = normalized_quote.split()
    if len(words) >= 6:
        fragment = " ".join(words[: max(6, len(words) // 2)])
        for chunk in chunks:
            if fragment in _normalize(chunk["text"]):
                return chunk["location"]

    return None
