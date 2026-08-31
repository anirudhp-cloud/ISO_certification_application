# Test case: reconstructs and writes out the EXACT consolidated prompt (system
# + user messages) that app/ai/openai_client.py:get_control_mappings sends to
# the LLM for one document — built the same way the real function builds it
# (base instructions + the real seeded ISO 42001 requirement catalog), so you
# can inspect exactly what the model receives.
#
# Run with:
#   backend/venv/Scripts/python tests/test_print_full_prompt.py
#
# Writes the full prompt to <repo_root>/full_prompt_iso42001.txt

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.requirement_catalog import format_requirements_listing  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.clause import Clause  # noqa: E402
from app.models.standard import Standard  # noqa: E402
from prompt_library import get_system_prompt  # noqa: E402

STANDARD_CODE = "iso42001"

# Stand-in for one document's extracted text (app/models/document_extraction.py
# .extracted_text) — swap this for real document text to test a real case.
SAMPLE_DOCUMENT_TEXT = (
    "This document is part of the organization's documented policy for AI systems. "
    "It specifically governs the DEVELOPMENT of AI systems: all AI systems developed "
    "by this organization must go through a documented design review, bias testing, "
    "and security review before release."
)

OUTPUT_FILE = Path(__file__).resolve().parent.parent.parent / f"full_prompt_{STANDARD_CODE}.txt"


def build_system_prompt(db, standard_code: str) -> str:
    """Identical construction to app/ai/openai_client.py:get_control_mappings."""
    standard = db.query(Standard).filter_by(code=standard_code).one()
    clauses = db.query(Clause).filter(Clause.standard_id == standard.id).order_by(Clause.code).all()
    return get_system_prompt(standard_code) + "\n\n" + format_requirements_listing(clauses)


def main() -> None:
    db = SessionLocal()
    try:
        system_prompt = build_system_prompt(db, STANDARD_CODE)
    finally:
        db.close()

    full_text = "\n".join([
        "=" * 100,
        "SYSTEM MESSAGE  (role: system)",
        "=" * 100,
        system_prompt,
        "",
        "=" * 100,
        "USER MESSAGE  (role: user — this document's extracted text)",
        "=" * 100,
        SAMPLE_DOCUMENT_TEXT,
    ])

    OUTPUT_FILE.write_text(full_text, encoding="utf-8")

    print(f"Standard: {STANDARD_CODE}")
    print(f"System message: {len(system_prompt)} chars (~{len(system_prompt) // 4} tokens)")
    print(f"User message:   {len(SAMPLE_DOCUMENT_TEXT)} chars")
    print(f"Written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
