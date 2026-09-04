"""add clauses.obligations and evidence_mappings.obligation_verdicts

The mark scheme, and the answers to it.

Before this, the model returned one coverage percentage per (document, requirement)
with nothing behind it. Measured over 1,057 real mappings: only 30 distinct values
appeared out of 101, 98% were a multiple of 5, and a document evidencing 1 of clause
7.5.2's 3 obligations was scored 100%. The number was a guess, and no explanation of
it could be anything but decoration.

Now each requirement carries its obligations, the model returns a verdict plus a
quote per obligation, and coverage is computed from those verdicts in code.

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clauses", sa.Column("obligations", postgresql.ARRAY(sa.Text()), nullable=True))

    # [{"index": 0, "verdict": "met"|"partial"|"unmet", "quote": ..., "source_location": ...}]
    # One entry per obligation the model was asked about. coverage_score is retained
    # but is now COMPUTED from these rather than supplied by the model.
    op.add_column(
        "evidence_mappings",
        sa.Column("obligation_verdicts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # relevance_score was a second guessed percentage — "how related is this document
    # to this requirement" — on top of the guessed coverage. Mapping is now derived:
    # a document maps to a requirement when it satisfies at least one obligation, so
    # there is nothing left for the field to say.
    op.drop_column("evidence_mappings", "relevance_score")


def downgrade() -> None:
    op.add_column(
        "evidence_mappings", sa.Column("relevance_score", sa.Numeric(precision=5, scale=2), nullable=True)
    )
    op.drop_column("evidence_mappings", "obligation_verdicts")
    op.drop_column("clauses", "obligations")
