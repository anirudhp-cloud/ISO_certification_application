# Document endpoints — upload / share-path / zip variants, list, versions, soft-delete.

import logging
import uuid
import zipfile
from dataclasses import dataclass
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai.requirement_catalog import split_by_segment
from app.extraction.document_extraction import SUPPORTED_EXTENSIONS
from app.crud.document import (
    add_document_version,
    create_document,
    get_document,
    list_current_documents,
    list_versions,
    soft_delete_document_group,
)
from app.crud.document_extraction import get_extraction_for_document
from app.crud.evidence_mapping import latest_run_for_organization, list_for_document
from app.deps import (
    get_db,
    require_auditor_document_access,
    require_document_access,
    require_document_group_access,
    require_org_access,
)
from app.models.clause import Clause
from app.models.standard import Standard
from app.models.user import User
from app.schemas.document import (
    DocumentRead,
    DocumentShareReference,
    DocumentVersionRead,
    SkippedZipEntry,
    ZipUploadResult,
)
from app.schemas.document_extraction import DocumentExtractionRead
from app.schemas.evidence_mapping import (
    DocumentMappingsRead,
    RequirementMappingRead,
    SegmentMappingsRead,
)
from app.storage.local import LocalStorageBackend
from app.tasks.extract_document import run_extraction

logger = logging.getLogger(f"iso_platform.{__name__}")
router = APIRouter()
storage = LocalStorageBackend()


def _extract_best_effort(db: Session, document) -> None:
    # Extraction failure (unsupported format, unreachable share path, corrupt
    # file) must never block the upload itself — it just means no extracted
    # text is available yet for the analysis pass to consume.
    try:
        run_extraction(db, document)
    except Exception:
        logger.exception("extraction failed for document %s (%s)", document.id, document.file_name)


def _storage_path(organization_id: uuid.UUID, document_group_id: uuid.UUID, version_number: int, file_name: str) -> str:
    return f"{organization_id}/{document_group_id}/v{version_number}_{file_name}"


# Archive noise that must never become a document: OS metadata, thumbnail caches,
# resource forks, and anything hidden.
_ZIP_JUNK_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}
_ZIP_JUNK_PREFIXES = ("__macosx/", ".")


@dataclass
class ZipEntry:
    path: str  # full path inside the archive, e.g. "HR Recruitment App/10.Foo.docx"
    file_name: str  # just the file, e.g. "10.Foo.docx"
    folder: str  # containing folder inside the archive, "" at the top level
    document_name: str
    document_type: str
    extension: str


def _infer_document_type(file_name: str) -> str:
    """Best-effort type from the filename.

    The old zip path stamped every entry "Zip Import", which is the same for 42
    documents and therefore says nothing. These names are meaningful on a controlled
    document set — "…_Procedure", "…_Policy", "…_Manual" — so read them. Ordered most
    specific first, since several names contain more than one keyword.
    """
    lowered = file_name.lower()
    for keyword, label in (
        ("applicability", "Statement of Applicability"),
        ("checklist", "Checklist"),
        ("procedure", "Procedure"),
        ("policy", "Policy"),
        ("manual", "Manual"),
        ("framework", "Framework"),
        ("guideline", "Guidelines"),
        ("objective", "Objectives"),
        ("register", "Register"),
        ("control", "Controls"),
        ("scope", "Scope"),
        ("statement", "Statement"),
        ("report", "Report"),
        ("record", "Record"),
    ):
        if keyword in lowered:
            return label
    return "Document"


def _zip_entries(archive: zipfile.ZipFile) -> list[ZipEntry]:
    """Parse an archive into candidate documents, preserving folder context.

    The folder path is the point. The old code did `name.rsplit("/", 1)[-1]` and threw
    the folder away, so two files with the same name in different folders became two
    documents with the same document_name — indistinguishable in the findings list and
    in every citation. On a real ISO 42001 set that is not cosmetic: per-AI-system
    procedures live in per-system folders, so the folder says WHICH system's lifecycle
    a document describes.

    Including the folder for nested entries also guarantees uniqueness within the
    archive: two entries cannot share a full path, so differing folders give differing
    names, and a top-level entry never collides with a nested one.
    """
    entries = []
    for path in archive.namelist():
        if path.endswith("/"):  # directory entry
            continue
        file_name = path.rsplit("/", 1)[-1]
        folder = path.rsplit("/", 1)[0] if "/" in path else ""
        stem = file_name.rsplit(".", 1)[0] if "." in file_name else file_name
        entries.append(
            ZipEntry(
                path=path,
                file_name=file_name,
                folder=folder,
                # Folder appended, not prepended, so the document's own number still
                # leads and the set sorts the way the numbering intends.
                document_name=f"{stem} — {folder}" if folder else stem,
                document_type=_infer_document_type(file_name),
                extension=file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "",
            )
        )
    return entries


def _reject_reason(entry: ZipEntry) -> str | None:
    """Why this entry can't become a document, or None if it can."""
    lowered = entry.file_name.lower()
    if lowered in _ZIP_JUNK_NAMES or lowered.startswith(_ZIP_JUNK_PREFIXES):
        return "operating-system metadata, not a document"
    if entry.path.lower().startswith(_ZIP_JUNK_PREFIXES):
        return "operating-system metadata, not a document"
    if not entry.extension:
        return "no file extension — cannot determine how to read it"
    if entry.extension not in SUPPORTED_EXTENSIONS:
        return (
            f".{entry.extension} cannot be read (supported: "
            f"{', '.join(sorted(SUPPORTED_EXTENSIONS))})"
        )
    return None


def _combine_standards(primary: str, additional: list[str]) -> list[str]:
    """The URL's own standard always comes first and is always included —
    `additional` just tags the same upload onto other standards too."""
    return [primary, *(s for s in additional if s != primary)]


@router.get("/organizations/{organization_id}/standards/{standard}/documents", response_model=list[DocumentRead])
def get_documents(
    organization_id: uuid.UUID,
    standard: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_access),
) -> list[DocumentRead]:
    return list_current_documents(db, organization_id=organization_id, certification_standard=standard)


@router.post("/organizations/{organization_id}/standards/{standard}/documents/upload", response_model=DocumentRead)
def upload_document(
    organization_id: uuid.UUID,
    standard: str,
    document_name: str = Form(...),
    document_type: str = Form(...),
    additional_standards: list[str] = Form([]),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_access),
) -> DocumentRead:
    content = file.file.read()
    # document_group_id isn't known until the row is created, so store under
    # a temp group id and rename isn't needed — create_document generates
    # its own group id; we build the storage path after, using that id.
    doc = create_document(
        db,
        organization_id=organization_id,
        certification_standards=_combine_standards(standard, additional_standards),
        document_name=document_name,
        document_type=document_type,
        source_type="upload",
        file_name=file.filename,
        storage_path="",  # placeholder, filled in right below
        submitted_by=current_user.id,
    )
    doc.storage_path = _storage_path(organization_id, doc.document_group_id, doc.version_number, file.filename)
    storage.save(doc.storage_path, content)
    db.commit()
    db.refresh(doc)
    logger.info(
        "document uploaded: %s (%s) by %s for org %s, standards=%s",
        doc.id, doc.file_name, current_user.id, organization_id, doc.certification_standards,
    )
    _extract_best_effort(db, doc)
    return doc


@router.post(
    "/organizations/{organization_id}/standards/{standard}/documents/share-path", response_model=DocumentRead
)
def add_share_path_reference(
    organization_id: uuid.UUID,
    standard: str,
    payload: DocumentShareReference,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_access),
) -> DocumentRead:
    # No bytes transferred or stored — storage_path *is* the shared/network path itself.
    doc = create_document(
        db,
        organization_id=organization_id,
        certification_standards=_combine_standards(standard, payload.additional_standards),
        document_name=payload.document_name,
        document_type=payload.document_type,
        source_type="share_path",
        file_name=payload.file_name,
        storage_path=payload.share_path,
        submitted_by=current_user.id,
    )
    logger.info(
        "document uploaded (share-path): %s (%s) by %s for org %s, standards=%s",
        doc.id, doc.file_name, current_user.id, organization_id, doc.certification_standards,
    )
    _extract_best_effort(db, doc)
    return doc


@router.post("/organizations/{organization_id}/standards/{standard}/documents/zip", response_model=ZipUploadResult)
def upload_zip(
    organization_id: uuid.UUID,
    standard: str,
    additional_standards: list[str] = Form([]),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_access),
) -> ZipUploadResult:
    content = file.file.read()
    try:
        archive = zipfile.ZipFile(BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Not a valid zip file")

    standards = _combine_standards(standard, additional_standards)
    entries = _zip_entries(archive)
    existing_names = {
        d.document_name
        for d in list_current_documents(
            db, organization_id=organization_id, certification_standard=standard
        )
    }

    created: list = []
    skipped: list[SkippedZipEntry] = []

    for entry in entries:
        # Junk and unreadable entries are rejected up front and reported, rather than
        # becoming documents whose extraction silently yields nothing — a zero-text
        # document looks identical to real evidence in the list, then contributes
        # nothing and makes its requirements read as uncovered.
        reason = _reject_reason(entry)
        if reason:
            skipped.append(SkippedZipEntry(path=entry.path, reason=reason))
            continue

        # One try per entry: a single bad file must not abort the other 41.
        try:
            doc = create_document(
                db,
                organization_id=organization_id,
                certification_standards=standards,
                document_name=entry.document_name,
                document_type=entry.document_type,
                source_type="zip",
                file_name=entry.file_name,
                storage_path="",
                submitted_by=current_user.id,
            )
            doc.storage_path = _storage_path(
                organization_id, doc.document_group_id, doc.version_number, entry.file_name
            )
            storage.save(doc.storage_path, archive.read(entry.path))
            db.commit()
            db.refresh(doc)
        except Exception as exc:
            db.rollback()
            skipped.append(SkippedZipEntry(path=entry.path, reason=f"{type(exc).__name__}: {exc}"))
            logger.exception("zip upload: failed on %s", entry.path)
            continue

        _extract_best_effort(db, doc)
        created.append(doc)

    # Uploading the same archive twice would silently double the document set and
    # double the cost of the next Analyze, so say so rather than let it pass.
    duplicates = sorted(d.document_name for d in created if d.document_name in existing_names)

    logger.info(
        "zip upload: %d document(s) created, %d skipped, %d name(s) already present — by %s for org %s, standards=%s",
        len(created), len(skipped), len(duplicates), current_user.id, organization_id, standards,
    )
    for entry in skipped:
        logger.warning("zip upload skipped %s — %s", entry.path, entry.reason)

    return ZipUploadResult(created=created, skipped=skipped, duplicate_names=duplicates)


@router.get("/documents/{document_group_id}/versions", response_model=list[DocumentVersionRead])
def get_document_versions(
    document_group_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_document_group_access),
) -> list[DocumentVersionRead]:
    return list_versions(db, document_group_id=document_group_id)


@router.post("/documents/{document_group_id}/versions", response_model=DocumentRead)
def post_document_version(
    document_group_id: uuid.UUID,
    document_name: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_document_group_access),
) -> DocumentRead:
    content = file.file.read()
    versions = list_versions(db, document_group_id=document_group_id)
    if not versions:
        raise HTTPException(status_code=404, detail="No such document group")
    current = versions[0]
    storage_path = _storage_path(current.organization_id, document_group_id, current.version_number + 1, file.filename)
    storage.save(storage_path, content)
    new_version = add_document_version(
        db,
        document_group_id=document_group_id,
        source_type="upload",
        file_name=file.filename,
        storage_path=storage_path,
        updated_by=current_user.id,
    )
    logger.info("new version uploaded for document group %s by %s: v%d (%s)", document_group_id, current_user.id, new_version.version_number, new_version.file_name)
    _extract_best_effort(db, new_version)
    return new_version


@router.get("/documents/{document_id}/extraction", response_model=DocumentExtractionRead)
def get_document_extraction(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_document_access),
) -> DocumentExtractionRead:
    extraction = get_extraction_for_document(db, document_id)
    if extraction is None:
        raise HTTPException(status_code=404, detail="No extraction available for this document yet")
    return extraction


@router.get("/documents/{document_id}/mappings", response_model=DocumentMappingsRead)
def get_document_mappings(
    document_id: uuid.UUID,
    run_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor_document_access),
) -> DocumentMappingsRead:
    """This document's clause structure and control structure from its most recent
    analysis, or from `run_id` if one is named.

    Auditor-only. The scores here are unreviewed model output, and showing them to
    whoever submitted the document would imply a verdict no auditor has issued —
    and invite wording tuned until the number rises.

    Two empty segments mean different things depending on `run_id`: null means the
    document has never been analysed, non-null means it was read and matched nothing
    — which usually points at a misfiled document or the wrong standard tag, and is
    worth surfacing rather than showing as an empty list.
    """
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    standard_code = document.certification_standards[0] if document.certification_standards else None
    standard = db.query(Standard).filter_by(code=standard_code).one_or_none() if standard_code else None
    catalog = (
        db.query(Clause).filter(Clause.standard_id == standard.id).all() if standard is not None else []
    )
    segment_totals = {segment: len(rows) for segment, rows in split_by_segment(catalog).items()}

    rows = list_for_document(db, document_id=document_id, run_id=run_id)

    if rows:
        status, resolved_run_id = "matched", rows[0].run_id
    else:
        # No rows means either nobody has analysed this document, or a run read it and
        # found nothing — and a document with no mappings has nothing on it pointing at
        # a run. Infer from the organization's latest run: if it started after this
        # document existed, the document was in that run's document set and simply
        # matched nothing. See crud.latest_run_for_organization on why this is an
        # inference until analysis_runs (M4) records each run's documents.
        latest = (
            latest_run_for_organization(
                db, organization_id=document.organization_id, certification_standard=standard_code
            )
            if standard_code
            else None
        )
        if latest is not None and latest[1] >= document.submitted_at:
            status, resolved_run_id = "no_match", latest[0]
        else:
            status, resolved_run_id = "not_analysed", None

    by_segment: dict[str, list[RequirementMappingRead]] = {"clause": [], "control": []}
    for row in rows:
        by_segment[row.segment].append(
            RequirementMappingRead(
                code=row.clause.code,
                title=row.clause.title,
                category=row.clause.category,
                relevance_score=float(row.relevance_score) if row.relevance_score is not None else None,
                coverage_score=float(row.coverage_score) if row.coverage_score is not None else None,
                rationale=row.rationale,
                source_location=row.source_location,
                unmet_guidance_points=row.unmet_guidance_points or [],
                guidance_points_total=len(row.clause.implementation_guidance or []),
            )
        )

    return DocumentMappingsRead(
        document_id=document.id,
        document_name=document.document_name,
        file_name=document.file_name,
        version_number=document.version_number,
        certification_standard=standard_code or "",
        status=status,
        run_id=resolved_run_id,
        analysed_at=max((row.created_at for row in rows), default=None),
        clauses=SegmentMappingsRead(
            segment="clause",
            matched=len(by_segment["clause"]),
            total=segment_totals.get("clause", 0),
            mappings=by_segment["clause"],
        ),
        controls=SegmentMappingsRead(
            segment="control",
            matched=len(by_segment["control"]),
            total=segment_totals.get("control", 0),
            mappings=by_segment["control"],
        ),
    )


@router.delete("/documents/{document_group_id}")
def delete_document_group(
    document_group_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_document_group_access),
) -> dict:
    soft_delete_document_group(db, document_group_id=document_group_id, deleted_by=current_user.id)
    logger.info("document group %s deleted by %s", document_group_id, current_user.id)
    return {"status": "deleted"}
