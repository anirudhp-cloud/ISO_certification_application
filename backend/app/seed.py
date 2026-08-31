# One-off loader: reads seed_data/<standard>_requirements.json (project root)
# and upserts it into `standards` + `clauses`. Run with: python -m app.seed

import json
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models.clause import Clause
from app.models.standard import Standard

SEED_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "seed_data"

# Maps a seed file's internal "framework" code to the standard id used
# everywhere else in the app (frontend standards[].id, documents.certification_standard).
FRAMEWORK_TO_STANDARD_ID = {
    "ISO42001": "iso42001",
    "ISO27001": "iso27001",
    "ISO9001": "iso9001",
}


def load_seed_file(path: Path, db) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    standard_id = FRAMEWORK_TO_STANDARD_ID[data["framework"]]

    standard = db.query(Standard).filter_by(code=standard_id).one_or_none()
    if standard is None:
        standard = Standard(code=standard_id, name=data["framework_title"])
        db.add(standard)
        db.flush()  # need standard.id before creating clauses
    else:
        standard.name = data["framework_title"]

    for position, req in enumerate(data["requirements"], start=1):
        clause = db.query(Clause).filter_by(standard_id=standard.id, code=req["code"]).one_or_none()
        if clause is None:
            clause = Clause(standard_id=standard.id, code=req["code"])
            db.add(clause)
        clause.sort_order = position  # the seed file is already in standard order
        clause.requirement_type = req["requirement_type"]
        clause.category = req.get("category")
        clause.title = req["title"]
        clause.description = req.get("description")
        clause.evidence_requirements = req.get("evidence_requirements")
        clause.implementation_guidance = req.get("implementation_guidance")

    db.commit()
    print(f"Seeded {len(data['requirements'])} requirements for {standard_id}")


def main() -> None:
    Base.metadata.create_all(engine)  # no-op if tables already exist via Alembic
    db = SessionLocal()
    try:
        for path in sorted(SEED_DATA_DIR.glob("*_requirements.json")):
            load_seed_file(path, db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
