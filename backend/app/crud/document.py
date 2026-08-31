# DB access functions for Document — create/version/soft-delete, scoped by organization + standard.
#
# Mirrors the operation semantics in DATABASE_DESIGN.md Section 2:
# create starts a new document_group_id at version 1; a version bump never
# overwrites a row, it flips the old one to is_current=False and inserts a
# new one; delete is a soft delete applied to every row in the group.
#
# A document can be tagged with multiple standards at once (certification_standards,
# an array — see app/models/document.py) — both create and delete/reupload below
# cascade against every Finding referencing this document, regardless of which
# standard that finding belongs to, since one document's evidence can matter to
# clauses across more than one standard now.

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.document import Document
from app.models.finding import Finding

logger = logging.getLogger(f"iso_platform.{__name__}")


def create_document(
    db: Session,
    *,
    organization_id: uuid.UUID,
    certification_standards: list[str],
    document_name: str,
    document_type: str,
    source_type: str,
    file_name: str,
    storage_path: str,
    submitted_by: uuid.UUID,
) -> Document:
    doc = Document(
        organization_id=organization_id,
        certification_standards=certification_standards,
        document_group_id=uuid.uuid4(),
        version_number=1,
        is_current=True,
        document_name=document_name,
        document_type=document_type,
        source_type=source_type,
        file_name=file_name,
        storage_path=storage_path,
        submitted_by=submitted_by,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _findings_referencing_document(db: Session, *, organization_id: uuid.UUID, document_id: uuid.UUID) -> list[Finding]:
    return (
        db.query(Finding)
        .filter(
            Finding.organization_id == organization_id,
            or_(Finding.evidence_document_id == document_id, Finding.evidence_document_ids.contains([document_id])),
        )
        .all()
    )


def add_document_version(
    db: Session,
    *,
    document_group_id: uuid.UUID,
    source_type: str,
    file_name: str,
    storage_path: str,
    updated_by: uuid.UUID,
) -> Document:
    current = (
        db.query(Document)
        .filter(Document.document_group_id == document_group_id, Document.is_current.is_(True))
        .one()
    )
    current.is_current = False

    new_version = Document(
        organization_id=current.organization_id,
        certification_standards=current.certification_standards,
        document_group_id=current.document_group_id,
        version_number=current.version_number + 1,
        is_current=True,
        previous_version_id=current.id,
        document_name=current.document_name,
        document_type=current.document_type,
        source_type=source_type,
        file_name=file_name,
        storage_path=storage_path,
        submitted_by=current.submitted_by,
        submitted_at=current.submitted_at,
        updated_by=updated_by,
    )
    db.add(new_version)
    db.flush()

    # Reupload override: a review already based on the OLD version's evidence
    # is stale now that the file changed underneath it — flip it back to
    # unreviewed. An already-unreviewed finding just stays as-is.
    reset_count = 0
    for finding in _findings_referencing_document(db, organization_id=current.organization_id, document_id=current.id):
        if finding.mapping_method == "reviewed":
            finding.mapping_method = "unreviewed"
            reset_count += 1
    if reset_count:
        logger.info("reupload of %s invalidated %d previously-reviewed finding(s)", current.id, reset_count)

    db.commit()
    db.refresh(new_version)
    return new_version


def soft_delete_document_group(db: Session, *, document_group_id: uuid.UUID, deleted_by: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    documents = db.query(Document).filter(Document.document_group_id == document_group_id).all()
    if not documents:
        return

    for document in documents:
        document.is_deleted = True
        document.deleted_by = deleted_by
        document.deleted_at = now

    # Cascade: strip this group's document ids out of every finding's evidence,
    # regardless of review status — a deleted document shouldn't silently keep
    # backing a finding, approved or not. If nothing else backed it, the
    # finding reverts to not_assessed entirely.
    organization_id = documents[0].organization_id
    document_ids = {d.id for d in documents}
    reset_count = 0
    for document_id in document_ids:
        for finding in _findings_referencing_document(db, organization_id=organization_id, document_id=document_id):
            remaining = [d for d in (finding.evidence_document_ids or []) if d not in document_ids]
            if not remaining:
                db.delete(finding)
                reset_count += 1
                continue
            finding.evidence_document_ids = remaining
            if finding.evidence_document_id in document_ids:
                finding.evidence_document_id = remaining[0]
    if reset_count:
        logger.info("delete of document group %s reset %d finding(s) to not_assessed", document_group_id, reset_count)

    db.commit()


def list_current_documents(db: Session, *, organization_id: uuid.UUID, certification_standard: str) -> list[Document]:
    return (
        db.query(Document)
        .options(joinedload(Document.submitted_by_user), joinedload(Document.updated_by_user))
        .filter(
            Document.organization_id == organization_id,
            Document.certification_standards.contains([certification_standard]),
            Document.is_current.is_(True),
            Document.is_deleted.is_(False),
        )
        .order_by(Document.document_name)
        .all()
    )


def list_versions(db: Session, *, document_group_id: uuid.UUID) -> list[Document]:
    return (
        db.query(Document)
        .options(joinedload(Document.submitted_by_user), joinedload(Document.updated_by_user))
        .filter(Document.document_group_id == document_group_id)
        .order_by(Document.version_number.desc())
        .all()
    )


def get_document(db: Session, document_id: uuid.UUID) -> Document | None:
    return db.get(Document, document_id)


def get_documents_by_ids(db: Session, document_ids: list[uuid.UUID]) -> dict[uuid.UUID, Document]:
    """Bulk lookup for resolving Finding.evidence_document_ids to display names
    (see app/api/routes/findings.py) without one query per finding."""
    if not document_ids:
        return {}
    rows = db.query(Document).filter(Document.id.in_(document_ids)).all()
    return {row.id: row for row in rows}
