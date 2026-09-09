"""Add geospatial and confidence fields to telemetry events

Revision ID: af4253fe208d
Revises: da4619e9de09
Create Date: 2026-09-09 12:11:54.473197

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "af4253fe208d"
down_revision: str | Sequence[str] | None = "da4619e9de09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("telemetry_events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("object_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("longitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("altitude_m", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("grid", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("confidence", sa.Float(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_telemetry_events_object_id"),
            ["object_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("telemetry_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_telemetry_events_object_id"))
        batch_op.drop_column("confidence")
        batch_op.drop_column("grid")
        batch_op.drop_column("altitude_m")
        batch_op.drop_column("longitude")
        batch_op.drop_column("latitude")
        batch_op.drop_column("object_id")
