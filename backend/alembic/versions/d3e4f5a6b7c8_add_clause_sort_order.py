"""add clauses.sort_order

Requirements were ordered by (category, code), both VARCHAR, so the findings page
sorted them as text: "10 Improvement" came before "4 Context of the organization",
and "A.10 Third-party" before "A.2 Policies related to AI". Parsing codes like
"A.6.2.8" in SQL is worse than carrying an explicit integer, so this adds one and
app/seed.py populates it from the seed file's own (correct) order.

Backfilled here for existing rows so the column can be NOT NULL without requiring a
re-seed first: ISO clauses sort ahead of Annex A controls, then by the numeric parts
of the code.

Revision ID: d3e4f5a6b7c8
Revises: b2c3d4e5f6a7
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clauses", sa.Column("sort_order", sa.Integer(), nullable=True))

    # Backfill: 'clause' rows first, then 'control' rows; within each, by the code's
    # numeric segments so 4.1 < 4.2 < 10.1 and A.2.2 < A.6.1.2 < A.10.2.
    op.execute(
        """
        WITH ordered AS (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY standard_id
                    ORDER BY
                        CASE WHEN requirement_type = 'clause' THEN 0 ELSE 1 END,
                        string_to_array(regexp_replace(code, '^A\\.', ''), '.')::int[]
                ) AS position
            FROM clauses
        )
        UPDATE clauses SET sort_order = ordered.position
        FROM ordered WHERE clauses.id = ordered.id
        """
    )

    op.alter_column("clauses", "sort_order", nullable=False)
    op.create_index("ix_clauses_standard_sort_order", "clauses", ["standard_id", "sort_order"])


def downgrade() -> None:
    op.drop_index("ix_clauses_standard_sort_order", table_name="clauses")
    op.drop_column("clauses", "sort_order")
