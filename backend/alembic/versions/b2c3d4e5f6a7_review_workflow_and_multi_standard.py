"""simplify mapping_method to unreviewed/reviewed, multi-standard documents, extraction chunks

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- findings.mapping_method: auto/confirmed/manual -> unreviewed/reviewed ---
    # Drop the old constraint FIRST — the data update below would otherwise
    # violate it the instant a row's new value isn't in the old 3-value list.
    op.drop_constraint('ck_findings_mapping_method', 'findings', type_='check')
    op.execute("UPDATE findings SET mapping_method = 'unreviewed' WHERE mapping_method = 'auto'")
    op.execute("UPDATE findings SET mapping_method = 'reviewed' WHERE mapping_method IN ('confirmed', 'manual')")
    op.create_check_constraint(
        'ck_findings_mapping_method', 'findings', "mapping_method IN ('unreviewed', 'reviewed')"
    )
    op.alter_column('findings', 'mapping_method', server_default='unreviewed')

    # --- documents.certification_standard (single) -> certification_standards (array) ---
    op.add_column('documents', sa.Column('certification_standards', postgresql.ARRAY(sa.String(20)), nullable=True))
    op.execute("UPDATE documents SET certification_standards = ARRAY[certification_standard]")
    op.alter_column('documents', 'certification_standards', nullable=False)
    op.drop_column('documents', 'certification_standard')

    # --- document_extractions: position-tagged chunks for deterministic source citation ---
    op.add_column('document_extractions', sa.Column('extracted_chunks', postgresql.JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('document_extractions', 'extracted_chunks')

    op.add_column('documents', sa.Column('certification_standard', sa.String(20), nullable=True))
    op.execute("UPDATE documents SET certification_standard = certification_standards[1]")
    op.alter_column('documents', 'certification_standard', nullable=False)
    op.drop_column('documents', 'certification_standards')

    op.drop_constraint('ck_findings_mapping_method', 'findings', type_='check')
    op.execute("UPDATE findings SET mapping_method = 'auto' WHERE mapping_method = 'unreviewed'")
    op.execute("UPDATE findings SET mapping_method = 'confirmed' WHERE mapping_method = 'reviewed'")
    op.create_check_constraint(
        'ck_findings_mapping_method', 'findings', "mapping_method IN ('auto', 'confirmed', 'manual')"
    )
    op.alter_column('findings', 'mapping_method', server_default='auto')
