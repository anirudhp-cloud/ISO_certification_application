# DB access for DocumentExtraction / DocumentExtractedImage — one extraction row
# per document version, created/replaced by tasks/extract_document.py.

import uuid

from sqlalchemy.orm import Session

from app.models.document_extracted_image import DocumentExtractedImage
from app.models.document_extraction import DocumentExtraction


def get_extraction_for_document(db: Session, document_id: uuid.UUID) -> DocumentExtraction | None:
    return db.query(DocumentExtraction).filter(DocumentExtraction.document_id == document_id).one_or_none()


def get_extractions_for_documents(db: Session, document_ids: list[uuid.UUID]) -> dict[uuid.UUID, DocumentExtraction]:
    """Bulk lookup — used to resolve a finding's source_location (see
    app/ai/source_locator.py) without one query per finding."""
    if not document_ids:
        return {}
    rows = db.query(DocumentExtraction).filter(DocumentExtraction.document_id.in_(document_ids)).all()
    return {row.document_id: row for row in rows}


def save_extraction(
    db: Session,
    *,
    document_id: uuid.UUID,
    extraction_method: str,
    extracted_text: str,
    images: list[tuple[int | None, str | None]],
    extracted_chunks: list[dict] | None = None,
) -> DocumentExtraction:
    """Creates the extraction row for this document version, replacing any prior
    attempt for the same document_id (document_id is unique — one extraction per version)."""
    existing = get_extraction_for_document(db, document_id)
    if existing is not None:
        db.delete(existing)
        db.flush()

    extraction = DocumentExtraction(
        document_id=document_id,
        extraction_method=extraction_method,
        extracted_text=extracted_text,
        extracted_chunks=extracted_chunks,
    )
    db.add(extraction)
    db.flush()

    for page_number, ocr_text in images:
        db.add(
            DocumentExtractedImage(
                document_extraction_id=extraction.id,
                page_number=page_number,
                ocr_text=ocr_text,
            )
        )

    db.commit()
    db.refresh(extraction)
    return extraction
