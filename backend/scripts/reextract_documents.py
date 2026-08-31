# Backfill: re-run extraction over documents already in the database.
#
# Why this exists: extraction happens at upload time (api/routes/documents.py),
# so every document stored before the M0 docx fix has wrong chunk locations
# persisted in document_extractions — paragraph numbers drifted from the real
# position, and tables were relocated to the end of the document. Fixing the
# extractor doesn't retroactively fix stored rows; this does.
#
# No LLM calls and no cost — this only re-reads the stored file and rewrites the
# extraction row. But note the flat text changes too (table order), so any gap
# analysis run before this backfill is not comparable to one run after it:
# re-analyse once this has finished.
#
# Usage, from backend/:
#     python -m scripts.reextract_documents --dry-run          # report only
#     python -m scripts.reextract_documents --ext docx         # just Word files
#     python -m scripts.reextract_documents                    # all documents

import argparse
import logging
import sys

from app.database import SessionLocal
from app.logging_setup import setup_logging
from app.models.document import Document
from app.tasks.extract_document import run_extraction

logger = logging.getLogger("iso_platform.reextract")


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-run extraction over stored documents.")
    parser.add_argument("--dry-run", action="store_true", help="list what would be re-extracted, change nothing")
    parser.add_argument(
        "--ext",
        action="append",
        metavar="EXT",
        help="only this file extension, without the dot (repeatable). Default: all supported types.",
    )
    args = parser.parse_args()

    setup_logging()
    wanted = {e.lower().lstrip(".") for e in args.ext} if args.ext else None

    db = SessionLocal()
    try:
        # Every version, not just is_current — a superseded version's extraction is
        # still what the version-history view shows, so it should be correct too.
        documents = db.query(Document).filter(Document.is_deleted.is_(False)).order_by(Document.document_name).all()

        selected = [
            d for d in documents if wanted is None or d.file_name.rsplit(".", 1)[-1].lower() in wanted
        ]
        skipped = len(documents) - len(selected)

        logger.info(
            "re-extraction: %d document(s) selected%s",
            len(selected),
            f", {skipped} skipped by --ext filter" if skipped else "",
        )

        succeeded = failed = 0
        for document in selected:
            label = f"{document.document_name} (v{document.version_number}, {document.file_name})"
            if args.dry_run:
                logger.info("would re-extract: %s", label)
                continue
            try:
                extraction = run_extraction(db, document)
                succeeded += 1
                logger.info(
                    "re-extracted %s — method=%s, %d chars, %d chunk(s)",
                    label,
                    extraction.extraction_method,
                    len(extraction.extracted_text or ""),
                    len(extraction.extracted_chunks or []),
                )
            except Exception:
                # One unreadable file (moved share path, corrupt upload) must not
                # abort the rest of the backfill.
                failed += 1
                logger.exception("re-extraction FAILED for %s", label)

        if args.dry_run:
            logger.info("dry run complete — nothing written")
        else:
            logger.info("re-extraction complete: %d succeeded, %d failed", succeeded, failed)
        return 1 if failed else 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
