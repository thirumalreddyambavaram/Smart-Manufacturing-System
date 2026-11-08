
"""add schedule metadata columns

Revision ID: 72ebf6b46435
Revises: 0cdcb04dee93
Create Date: 2026-11-07 11:15:53.679431
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision: str = "72ebf6b46435"
down_revision: Union[str, Sequence[str], None] = "0cdcb04dee93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add schedule metadata columns and constraints."""

    op.add_column(
        "operation_schedules",
        sa.Column(
            "schedule_code",
            sa.String(length=30),
            nullable=True
        )
    )

    op.add_column(
        "operation_schedules",
        sa.Column(
            "schedule_run_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.create_unique_constraint(
        "uq_operation_schedules_schedule_code",
        "operation_schedules",
        ["schedule_code"]
    )

    op.create_foreign_key(
        "fk_operation_schedules_schedule_run_id",
        "operation_schedules",
        "schedule_runs",
        ["schedule_run_id"],
        ["id"]
    )


def downgrade() -> None:
    """Remove schedule metadata columns and constraints."""

    op.drop_constraint(
        "fk_operation_schedules_schedule_run_id",
        "operation_schedules",
        type_="foreignkey"
    )

    op.drop_constraint(
        "uq_operation_schedules_schedule_code",
        "operation_schedules",
        type_="unique"
    )

    op.drop_column(
        "operation_schedules",
        "schedule_run_id"
    )

    op.drop_column(
        "operation_schedules",
        "schedule_code"
    )
