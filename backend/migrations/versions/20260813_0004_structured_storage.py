"""Add equipment archiving and structured temporary storage.

Revision ID: 20260813_0004
Revises: 20260812_0003
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260813_0004"
down_revision: str | None = "20260812_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_columns() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.add_column("equipments", sa.Column("archived_at", sa.DateTime(timezone=True)))
    op.add_column("equipments", sa.Column("archived_by_user_id", sa.Uuid()))
    op.add_column("equipments", sa.Column("archive_reason", sa.Text()))
    op.create_foreign_key(
        "fk_equipments_archived_by_user_id_users",
        "equipments",
        "users",
        ["archived_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_equipments_archived_at", "equipments", ["archived_at"])
    op.create_index(
        "ix_equipments_archived_by_user_id", "equipments", ["archived_by_user_id"]
    )

    op.create_table(
        "storage_locations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("warehouse", sa.String(120), nullable=False),
        sa.Column("aisle", sa.String(50)),
        sa.Column("rack", sa.String(50)),
        sa.Column("shelf", sa.String(50)),
        sa.Column("position", sa.String(50)),
        sa.Column("capacity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint("capacity > 0", name="ck_storage_locations_capacity"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_storage_locations_code", "storage_locations", ["code"], unique=True)
    op.create_index("ix_storage_locations_warehouse", "storage_locations", ["warehouse"])

    op.create_table(
        "storage_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column(
            "entered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["location_id"], ["storage_locations.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("equipment_id"),
    )
    op.create_index(
        "ix_storage_assignments_equipment_id",
        "storage_assignments",
        ["equipment_id"],
        unique=True,
    )
    op.create_index(
        "ix_storage_assignments_location_id", "storage_assignments", ["location_id"]
    )
    op.create_index("ix_storage_assignments_entered_at", "storage_assignments", ["entered_at"])

    op.create_table(
        "storage_movements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("from_location_id", sa.Uuid()),
        sa.Column("to_location_id", sa.Uuid()),
        sa.Column("movement_type", sa.String(20), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid()),
        sa.Column("notes", sa.Text()),
        sa.CheckConstraint(
            "movement_type IN ('ENTRY', 'TRANSFER', 'EXIT')",
            name="ck_storage_movements_type",
        ),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["from_location_id"], ["storage_locations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["to_location_id"], ["storage_locations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_storage_movements_equipment_id", "storage_movements", ["equipment_id"])
    op.create_index(
        "ix_storage_movements_from_location_id", "storage_movements", ["from_location_id"]
    )
    op.create_index(
        "ix_storage_movements_to_location_id", "storage_movements", ["to_location_id"]
    )
    op.create_index("ix_storage_movements_movement_type", "storage_movements", ["movement_type"])
    op.create_index("ix_storage_movements_occurred_at", "storage_movements", ["occurred_at"])
    op.create_index("ix_storage_movements_user_id", "storage_movements", ["user_id"])
    op.create_index(
        "ix_storage_movements_equipment_time",
        "storage_movements",
        ["equipment_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("storage_movements")
    op.drop_table("storage_assignments")
    op.drop_table("storage_locations")
    op.drop_index("ix_equipments_archived_by_user_id", table_name="equipments")
    op.drop_index("ix_equipments_archived_at", table_name="equipments")
    op.drop_constraint(
        "fk_equipments_archived_by_user_id_users", "equipments", type_="foreignkey"
    )
    op.drop_column("equipments", "archive_reason")
    op.drop_column("equipments", "archived_by_user_id")
    op.drop_column("equipments", "archived_at")
