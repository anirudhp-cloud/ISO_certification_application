"""add findings.obligation_rollup and drop findings.relevance_score

The requirement-level reasoning, computed rather than written by an LLM.

Replaces the reduce step's prose narrative. That text was prose ABOUT several
documents rather than a quote FROM one, so it could not be located in any document —
11 of 50 multi-document findings on a real run had no resolvable citation — and it
buried the audit question (which obligation does NO document satisfy?) inside a
paragraph. The rollup stores that structure directly.

relevance_score goes for the same reason it went from evidence_mappings: it was a
second guessed percentage on top of the guessed coverage, and mapping is now derived
from whether any obligation is satisfied.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "findings",
        sa.Column("obligation_rollup", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.drop_column("findings", "relevance_score")
    op.drop_column("findings", "previous_relevance_score")


def downgrade() -> None:
    op.add_column("findings", sa.Column("previous_relevance_score", sa.Numeric(5, 2), nullable=True))
    op.add_column("findings", sa.Column("relevance_score", sa.Numeric(5, 2), nullable=True))
    op.drop_column("findings", "obligation_rollup")
