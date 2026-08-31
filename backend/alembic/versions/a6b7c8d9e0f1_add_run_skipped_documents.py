"""add analysis_runs.skipped_documents

A document the run could not read must be recorded as *not read* — never as "read and
matched nothing". Without this column the two are indistinguishable: the run's
document_ids says the document was in scope, so the per-document view would report
`no_match`, and the coverage report would attribute that document's absent evidence to
the organisation rather than to a failed call.

That is the fallback to avoid. An absent result must not become an asserted one.

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # [{"document_id": ..., "document_name": ..., "error": ...}, ...] — the name and
    # error are captured at the time of failure so the coverage report can name what
    # was missed without re-resolving documents that may since have changed.
    op.add_column(
        "analysis_runs",
        sa.Column("skipped_documents", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("analysis_runs", "skipped_documents")
