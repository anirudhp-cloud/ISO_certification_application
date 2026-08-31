"""add annex b guidance fields to clauses and findings

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Annex B "Implementation guidance" bullets per Annex A control (the "how"
    # alongside clauses.description's Annex A "what") — NULL for clauses 4-10.
    op.add_column(
        'clauses',
        sa.Column('implementation_guidance', postgresql.ARRAY(sa.Text()), nullable=True),
    )
    # Subset of the above that the LLM judged unsatisfied by the evidence,
    # for the Gap Analysis checklist.
    op.add_column(
        'findings',
        sa.Column('unmet_guidance_points', postgresql.ARRAY(sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('findings', 'unmet_guidance_points')
    op.drop_column('clauses', 'implementation_guidance')
