"""add evidence_document_ids to findings

Revision ID: f1a2b3c4d5e6
Revises: c7bba91349e8
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'c7bba91349e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Holds every document that contributed evidence to a finding, for controls
    # where 2+ documents were combined by the reduce step. evidence_document_id
    # (existing, singular) stays as the primary/highest-scoring contributor.
    op.add_column(
        'findings',
        sa.Column('evidence_document_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('findings', 'evidence_document_ids')
