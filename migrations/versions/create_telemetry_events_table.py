"""Create telemetry events table

Revision ID: da4619e9de09
Revises:
Create Date: 2026-09-03 14:11:22.823131

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da4619e9de09"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "telemetry_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("classification", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("context", sa.String(), nullable=False),
        sa.Column("flagged", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("telemetry_events", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_telemetry_events_classification"),
            ["classification"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_telemetry_events_flagged"),
            ["flagged"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_telemetry_events_source"),
            ["source"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_telemetry_events_timestamp"),
            ["timestamp"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("telemetry_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_telemetry_events_timestamp"))
        batch_op.drop_index(batch_op.f("ix_telemetry_events_source"))
        batch_op.drop_index(batch_op.f("ix_telemetry_events_flagged"))
        batch_op.drop_index(batch_op.f("ix_telemetry_events_classification"))

    op.drop_table("telemetry_events")
