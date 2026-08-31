# Zip ingestion tests.
#
# The original handler did `name.rsplit("/", 1)[-1]` and threw the folder path away,
# so two files with the same name in different folders became two documents with the
# same document_name — indistinguishable in the findings list and in every citation.
# On the real 42-document set that hit 4 filenames, 8 files: per-AI-system procedures
# live in per-system folders, so the folder is what says WHICH system's lifecycle a
# document describes. Losing it makes a citation unusable as evidence.
#
# It also stamped every entry document_type="Zip Import" (identical for 42 documents,
# therefore meaningless), and turned OS junk and unreadable file types into documents
# whose extraction silently yielded nothing.

import io
import zipfile

from app.api.routes.documents import _infer_document_type, _reject_reason, _zip_entries


def _archive(paths: dict[str, bytes]) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for path, data in paths.items():
            z.writestr(path, data)
    buf.seek(0)
    return zipfile.ZipFile(buf)


def _accepted(archive):
    return [e for e in _zip_entries(archive) if not _reject_reason(e)]


# --- folder context is preserved --------------------------------------------


def test_same_filename_in_two_folders_yields_two_distinct_documents():
    archive = _archive(
        {
            "HR Recruitment App/10.System-Lifecycle-Management-Procedure.docx": b"a",
            "Vesta AI Companion/10.System-Lifecycle-Management-Procedure.docx": b"b",
        }
    )
    names = [e.document_name for e in _accepted(archive)]

    assert len(set(names)) == 2, f"names collided: {names}"
    assert any("HR Recruitment App" in n for n in names)
    assert any("Vesta AI Companion" in n for n in names)


def test_the_documents_own_number_still_leads_the_name():
    """The folder is appended, not prepended, so the controlled-document numbering
    still sorts the way it was designed to."""
    archive = _archive({"HR Recruitment App/10.System-Lifecycle.docx": b"a"})
    assert _accepted(archive)[0].document_name.startswith("10.")


def test_a_top_level_file_gets_no_folder_suffix():
    archive = _archive({"2A.AI_Policy for TechVest.docx": b"a"})
    entry = _accepted(archive)[0]
    assert entry.document_name == "2A.AI_Policy for TechVest"
    assert entry.folder == ""


def test_a_top_level_file_never_collides_with_a_nested_one_of_the_same_name():
    archive = _archive({"10.Foo.docx": b"a", "Vesta/10.Foo.docx": b"b"})
    names = [e.document_name for e in _accepted(archive)]
    assert len(set(names)) == 2


def test_the_original_filename_is_kept_separately():
    """document_name carries the disambiguation; file_name stays the real file, so the
    stored path and the meta line still show what was actually uploaded."""
    archive = _archive({"HR Recruitment App/10.System-Lifecycle.docx": b"a"})
    entry = _accepted(archive)[0]
    assert entry.file_name == "10.System-Lifecycle.docx"
    assert entry.document_name != entry.file_name


# --- junk and unreadable entries are rejected, with a reason ----------------


def test_os_metadata_is_rejected():
    archive = _archive(
        {
            "Thumbs.db": b"junk",
            "desktop.ini": b"junk",
            "__MACOSX/._2A.AI_Policy.docx": b"junk",
            ".DS_Store": b"junk",
            "2A.AI_Policy.docx": b"real",
        }
    )
    accepted = _accepted(archive)
    assert [e.file_name for e in accepted] == ["2A.AI_Policy.docx"]


def test_an_unreadable_file_type_is_rejected_with_the_supported_list():
    archive = _archive({"notes.md": b"x", "diagram.png": b"x"})
    entries = _zip_entries(archive)
    reasons = [_reject_reason(e) for e in entries]

    assert all(r is not None for r in reasons)
    assert all("cannot be read" in r and "docx" in r for r in reasons)


def test_a_file_with_no_extension_is_rejected():
    archive = _archive({"README": b"x"})
    assert _reject_reason(_zip_entries(archive)[0]) == (
        "no file extension — cannot determine how to read it"
    )


def test_every_supported_format_is_accepted():
    archive = _archive({f"doc.{ext}": b"x" for ext in ("txt", "docx", "pptx", "xlsx", "pdf")})
    assert len(_accepted(archive)) == 5


def test_directory_entries_are_not_documents():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("HR Recruitment App/", b"")
        z.writestr("HR Recruitment App/10.Foo.docx", b"a")
    buf.seek(0)
    assert len(_zip_entries(zipfile.ZipFile(buf))) == 1


# --- document_type is inferred, not a constant ------------------------------


def test_document_type_is_read_from_the_filename():
    cases = {
        "17.AI_Incident_Management_Procedure.docx": "Procedure",
        "2A.AI_Policy for TechVest.docx": "Policy",
        "31. Quality & AI _Manual_ for TechVest Global.docx": "Manual",
        "1B.AI Governance Framework for TechVest.docx": "Framework",
        "20.Ethical_AI_Responsible_AI_Guidelines.docx": "Guidelines",
        "36.Internal_Audit_Checklist_ISO9K_42K.docx": "Checklist",
        "5.AI & QMS SMART Objectives.docx": "Objectives",
        "1A.Scope of AIMS & QMS.docx": "Scope",
        "35.Statement_of_Applicability_ISO42001Annex A.xlsx": "Statement of Applicability",
        "11.AI System Design and Development Controls.docx": "Controls",
    }
    for file_name, expected in cases.items():
        assert _infer_document_type(file_name) == expected, file_name


def test_applicability_wins_over_statement():
    """Several names contain more than one keyword, so order matters — the SoA is a
    Statement of Applicability, not a generic Statement."""
    assert _infer_document_type("35.Statement_of_Applicability.xlsx") == "Statement of Applicability"
    assert _infer_document_type("38.Vision Mission & Values statement.pptx") == "Statement"


def test_an_unrecognised_name_falls_back_to_a_generic_type():
    assert _infer_document_type("40.Administration.docx") == "Document"


def test_no_entry_is_labelled_zip_import():
    """The old constant. Identical across 42 documents, so it carried no information."""
    archive = _archive({"HR/10.System-Lifecycle-Management-Procedure.docx": b"a"})
    assert _accepted(archive)[0].document_type != "Zip Import"


# --- the real archive shape -------------------------------------------------


def test_a_two_project_archive_produces_all_unique_names():
    """Mirrors the real set: shared numbering across two per-AI-system folders."""
    shared = ["10.System-Lifecycle.docx", "14.Change-Management.docx", "15.AI-Deployment.docx"]
    archive = _archive(
        {f"{folder}/{f}": b"x" for folder in ("HR Recruitment App", "Vesta AI Companion") for f in shared}
        | {"2A.AI_Policy.docx": b"x", "31.Quality_Manual.docx": b"x"}
    )
    names = [e.document_name for e in _accepted(archive)]

    assert len(names) == 8
    assert len(set(names)) == 8
