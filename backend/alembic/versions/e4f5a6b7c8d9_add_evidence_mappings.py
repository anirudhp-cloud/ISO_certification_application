"""add evidence_mappings

The per-document clause/control structure. Before this, the map step's results
lived in a local dict in run_gap_analysis, were reduced straight into findings and
then discarded — so nothing could answer "which clauses and controls does THIS
document satisfy?", and no record survived of what a past run actually read.

Grain differs from findings deliberately: findings are one row per (organization,
requirement), a rollup across every contributing document; these are one row per
(document, requirement).

run_id is a plain UUID rather than a foreign key until analysis_runs exists at M4.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clause_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("segment", sa.String(length=10), nullable=False),
        sa.Column("relevance_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("coverage_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("source_location", sa.String(length=160), nullable=True),
        sa.Column("unmet_guidance_points", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["clause_id"], ["clauses.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "document_id", "clause_id", name="uq_evidence_mappings_run_doc_clause"),
        sa.CheckConstraint("segment IN ('clause', 'control')", name="ck_evidence_mappings_segment"),
    )
    op.create_index("ix_evidence_mappings_run_segment", "evidence_mappings", ["run_id", "segment"])
    op.create_index("ix_evidence_mappings_document", "evidence_mappings", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_mappings_document", table_name="evidence_mappings")
    op.drop_index("ix_evidence_mappings_run_segment", table_name="evidence_mappings")
    op.drop_table("evidence_mappings")
