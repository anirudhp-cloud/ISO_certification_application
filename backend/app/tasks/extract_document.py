# Extraction pipeline — runs after a document (or a new version of one) is stored:
# format-routes to native extraction, falls back to OCR for scanned PDFs, pulls
# embedded images out for their own OCR pass, and persists a document_extractions
# row (+ document_extracted_images rows) per DATABASE_DESIGN.md / PHASE1_SCOPE.md.
#
# `run_extraction` is the actual logic, reusable from either caller:
#   - today: called directly, inline, right after documents.py stores the file —
#     no Redis is running locally yet, and Celery tasks are plain callables, so
#     calling the function body directly (not through .delay()) runs it
#     synchronously in-process with zero broker dependency.
#   - later: `extract_document_task.delay(document_id)` once Redis is up — at
#     that point extraction moves off the request path, which matters once OCR
#     calls are actually slow.

import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.crud.document_extraction import save_extraction
from app.database import SessionLocal
from app.extraction.document_intelligence_client import DocumentIntelligenceNotConfigured, ocr_image
from app.extraction.image_extractor import extract_images
from app.extraction.document_extraction import extract_text
from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from app.storage.local import LocalStorageBackend
from app.tasks.celery_app import celery_app

logger = logging.getLogger(f"iso_platform.{__name__}")
storage = LocalStorageBackend()


def _read_document_bytes(document: Document) -> bytes:
    if document.source_type == "share_path":
        # storage_path *is* the shared/network path itself — no bytes ever
        # passed through our storage backend for this ingestion method.
        return Path(document.storage_path).read_bytes()
    return storage.read(document.storage_path)


def run_extraction(db: Session, document: Document) -> DocumentExtraction:
    content = _read_document_bytes(document)

    try:
        extraction_method, extracted_text, extracted_chunks = extract_text(document.file_name, content)
    except DocumentIntelligenceNotConfigured:
        extraction_method, extracted_text, extracted_chunks = "ocr_unavailable", "", []
        logger.warning("extraction unavailable for %s (%s) — Document Intelligence not configured", document.id, document.file_name)

    images = []
    for image in extract_images(document.file_name, content):
        try:
            ocr_text = ocr_image(image.content)
        except DocumentIntelligenceNotConfigured:
            ocr_text = None
        images.append((image.page_number, ocr_text))

    logger.info(
        "extraction complete for %s (%s): method=%s, %d chars, %d embedded image(s)",
        document.id, document.file_name, extraction_method, len(extracted_text), len(images),
    )

    return save_extraction(
        db,
        document_id=document.id,
        extraction_method=extraction_method,
        extracted_text=extracted_text,
        extracted_chunks=extracted_chunks,
        images=images,
    )


@celery_app.task(name="extract_document")
def extract_document_task(document_id: str) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, uuid.UUID(document_id))
        if document is None:
            return
        run_extraction(db, document)
    finally:
        db.close()
