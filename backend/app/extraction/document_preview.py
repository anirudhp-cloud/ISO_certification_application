# Renders any stored document as a PDF the browser can display natively, with the
# cited passage highlighted in the real document.
#
# This replaces two worse attempts. First a list of extraction chunks — accurate, but
# it showed the parser's view (`Table 1, row 2 | Document ID | AIMS-QMS-010`), which is
# not how anyone reads a controlled document. Then docx-to-HTML via mammoth, which
# kept headings and tables but lost page layout, and had nothing to offer for .pptx or
# .xlsx at all.
#
# LibreOffice converts docx, pptx and xlsx to PDF with layout, tables and images
# intact, and every browser has a native PDF viewer. So there is exactly one code path
# for every format, and what an auditor sees is the document.
#
# Conversion costs ~2-12s (mostly LibreOffice start-up), so results are cached per
# document version. A document version never changes — a new upload is a new version
# with its own id — so the cache needs no invalidation.

import logging
import shutil
import subprocess
import uuid
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(f"iso_platform.{__name__}")

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "preview_cache"

# Formats LibreOffice converts. A .pdf needs no conversion; a .txt is wrapped.
CONVERTIBLE = {"docx", "doc", "pptx", "ppt", "xlsx", "xls", "odt", "odp", "ods", "rtf"}

_SOFFICE_CANDIDATES = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/usr/bin/libreoffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)

CONVERT_TIMEOUT_SECONDS = 120


class PreviewUnavailable(Exception):
    """No preview can be produced — LibreOffice missing, or the format isn't
    convertible. The caller falls back to offering the original file, which is always
    better than showing nothing."""


def soffice_path() -> str | None:
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    for candidate in _SOFFICE_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def can_preview(file_name: str) -> bool:
    extension = file_name.rsplit(".", 1)[-1].lower()
    if extension == "pdf":
        return True
    if extension == "txt":
        return True
    return extension in CONVERTIBLE and soffice_path() is not None


def _cache_path(document_id: uuid.UUID) -> Path:
    return CACHE_DIR / f"{document_id}.pdf"


def _convert_with_soffice(source: Path, target_dir: Path) -> Path:
    executable = soffice_path()
    if executable is None:
        raise PreviewUnavailable(
            "LibreOffice is not installed, so this format cannot be shown in the browser."
        )

    # -env:UserInstallation gives this conversion its own profile directory. Without
    # it, a soffice already open on the desktop makes the headless call exit
    # immediately without converting anything.
    profile = target_dir / "lo_profile"
    result = subprocess.run(
        [
            executable,
            "-env:UserInstallation=file:///" + str(profile).replace("\\", "/"),
            "--headless",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(target_dir),
            str(source),
        ],
        capture_output=True,
        text=True,
        timeout=CONVERT_TIMEOUT_SECONDS,
    )
    produced = target_dir / (source.stem + ".pdf")
    if not produced.exists():
        raise PreviewUnavailable(
            f"LibreOffice could not convert this file: {result.stderr.strip()[:200] or 'no output produced'}"
        )
    return produced


def build_preview(document_id: uuid.UUID, file_name: str, content: bytes) -> Path:
    """Return a path to this document as a PDF, converting and caching if needed."""
    cached = _cache_path(document_id)
    if cached.exists() and cached.stat().st_size > 0:
        return cached

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    extension = file_name.rsplit(".", 1)[-1].lower()
    work = CACHE_DIR / f"tmp_{document_id}"
    work.mkdir(parents=True, exist_ok=True)

    try:
        if extension == "pdf":
            cached.write_bytes(content)
            return cached

        if extension == "txt":
            # Laid out as a PDF like everything else, so the viewer has one code path.
            text = content.decode("utf-8", errors="replace")
            doc = fitz.open()
            page = doc.new_page()
            page.insert_textbox(
                fitz.Rect(56, 56, page.rect.width - 56, page.rect.height - 56),
                text,
                fontsize=10,
                fontname="cour",
            )
            doc.save(cached)
            doc.close()
            return cached

        source = work / file_name
        source.write_bytes(content)
        produced = _convert_with_soffice(source, work)
        shutil.move(str(produced), str(cached))
        logger.info("preview built for %s (%s)", document_id, file_name)
        return cached
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _search_lines(quote: str) -> list[str]:
    """Searchable fragments of a quote, longest first.

    The extractor collapses whitespace and joins table cells with " | "; neither
    survives into the PDF's text layer, so a whole-quote search fails on anything
    spanning a line or a table row. Searching the longest single line finds the
    passage without needing the extractor and LibreOffice to agree on layout.
    """
    lines = [line.strip() for line in quote.replace(" | ", "\n").splitlines()]
    return sorted((line for line in lines if len(line) >= 12), key=len, reverse=True)


def _annotate(page, rect, label: str | None) -> None:
    highlight = page.add_highlight_annot(rect)
    highlight.set_colors(stroke=(1, 0.87, 0.4))
    if label:
        # Carried in the annotation itself, so hovering a highlight in the browser's
        # own PDF viewer says which requirement it evidences. Without this, a
        # document with 30 highlights tells an auditor that something matched
        # everywhere and nothing about what.
        highlight.set_info(title="Evidence", content=label)
    highlight.update()


def highlight_all(pdf_path: Path, passages: list[dict]) -> tuple[bytes, list[dict]]:
    """Highlight every satisfying passage in one document, each labelled.

    `passages` are {"quote": str, "label": str} — one per obligation this document
    satisfies. Returns the PDF plus, for each passage, the page it was found on (or
    None). Reading a document with all of its evidence marked at once is how an
    auditor actually works through a file; clicking one citation at a time answers
    "where is this quote", not "what does this document prove".

    A passage that cannot be located is reported as found=False rather than dropped
    or approximated — an unlocatable quote is a fact about the extraction, and
    hiding it would leave the auditor believing they had seen everything.
    """
    document = fitz.open(pdf_path)
    try:
        located = []
        for passage in passages:
            quote = (passage.get("quote") or "").strip()
            label = passage.get("label")
            page_number = None
            if quote:
                for needle in _search_lines(quote)[:4]:
                    for index, page in enumerate(document):
                        rects = page.search_for(needle[:180], quads=False)
                        if not rects:
                            continue
                        for rect in rects:
                            _annotate(page, rect, label)
                        page_number = index + 1
                        break
                    if page_number:
                        break
            located.append({"label": label, "quote": quote, "page": page_number,
                            "found": page_number is not None})
        return document.tobytes(), located
    finally:
        document.close()


def highlight_quote(pdf_path: Path, quote: str | None) -> tuple[bytes, int | None]:
    """Return (pdf bytes, 1-based page number) with `quote` highlighted in place.

    Searches the converted PDF for the passage and adds a real highlight annotation,
    so the browser's own viewer shows the document with the cited text marked — not an
    approximation of it. Falls back to the unmarked PDF when the quote can't be found,
    which happens when the extractor's text and LibreOffice's layout disagree (a table
    cell split across lines, say).
    """
    content, located = highlight_all(pdf_path, [{"quote": quote, "label": None}] if quote else [])
    return content, (located[0]["page"] if located else None)
