"""Create equipment catalogs, registration, collection and traceability tables.

Revision ID: 20260812_0002
Revises: 20260812_0001
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260812_0002"
down_revision: str | None = "20260812_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_columns() -> list[sa.Column]:
    return [
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
    ]


def create_catalog_table(table_name: str, code_index_name: str) -> None:
    op.create_table(
        table_name,
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(code_index_name, table_name, ["code"], unique=True)


def upgrade() -> None:
    create_catalog_table("equipment_categories", "ix_equipment_categories_code")
    create_catalog_table("equipment_types", "ix_equipment_types_code")
    create_catalog_table("sectors", "ix_sectors_code")

    op.create_table(
        "number_sequences",
        sa.Column("namespace", sa.String(length=50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("current_value", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("namespace", "year"),
        sa.UniqueConstraint("namespace", "year", name="uq_number_sequence"),
    )

    op.create_table(
        "equipments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tracking_code", sa.String(length=20), nullable=False),
        sa.Column("asset_number", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=150), nullable=True),
        sa.Column("equipment_type_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("origin_sector_id", sa.Uuid(), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("initial_condition", sa.String(length=255), nullable=False),
        sa.Column("current_status", sa.String(length=50), nullable=False),
        sa.Column("collection_date", sa.DateTime(timezone=True), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["equipment_categories.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["equipment_type_id"],
            ["equipment_types.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["origin_sector_id"],
            ["sectors.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_number"),
        sa.UniqueConstraint("tracking_code"),
    )
    op.create_index("ix_equipments_asset_number", "equipments", ["asset_number"], unique=True)
    op.create_index("ix_equipments_brand", "equipments", ["brand"], unique=False)
    op.create_index("ix_equipments_brand_model", "equipments", ["brand", "model"], unique=False)
    op.create_index("ix_equipments_category_id", "equipments", ["category_id"], unique=False)
    op.create_index(
        "ix_equipments_collection_date",
        "equipments",
        ["collection_date"],
        unique=False,
    )
    op.create_index("ix_equipments_current_status", "equipments", ["current_status"], unique=False)
    op.create_index(
        "ix_equipments_equipment_type_id",
        "equipments",
        ["equipment_type_id"],
        unique=False,
    )
    op.create_index("ix_equipments_model", "equipments", ["model"], unique=False)
    op.create_index(
        "ix_equipments_origin_sector_id",
        "equipments",
        ["origin_sector_id"],
        unique=False,
    )
    op.create_index("ix_equipments_serial_number", "equipments", ["serial_number"], unique=False)
    op.create_index("ix_equipments_tracking_code", "equipments", ["tracking_code"], unique=True)

    op.create_table(
        "collections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("collector_user_id", sa.Uuid(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["collector_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("equipment_id"),
    )
    op.create_index("ix_collections_collector_user_id", "collections", ["collector_user_id"])
    op.create_index("ix_collections_equipment_id", "collections", ["equipment_id"], unique=True)

    op.create_table(
        "equipment_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("previous_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipment_events_equipment_id", "equipment_events", ["equipment_id"])
    op.create_index(
        "ix_equipment_events_equipment_time",
        "equipment_events",
        ["equipment_id", "occurred_at"],
    )
    op.create_index("ix_equipment_events_event_type", "equipment_events", ["event_type"])
    op.create_index("ix_equipment_events_occurred_at", "equipment_events", ["occurred_at"])
    op.create_index("ix_equipment_events_user_id", "equipment_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("equipment_events")
    op.drop_table("collections")
    op.drop_table("equipments")
    op.drop_table("number_sequences")
    op.drop_table("sectors")
    op.drop_table("equipment_types")
    op.drop_table("equipment_categories")
