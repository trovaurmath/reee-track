"""Add configurable triage and classification.

Revision ID: 20260812_0003
Revises: 20260812_0002
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260812_0003"
down_revision: str | None = "20260812_0002"
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
    op.create_table(
        "triage_classifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("target_status", sa.String(length=50), nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "ix_triage_classifications_code",
        "triage_classifications",
        ["code"],
        unique=True,
    )

    op.create_table(
        "triage_criteria",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("question", sa.String(length=255), nullable=False),
        sa.Column("help_text", sa.String(length=255), nullable=True),
        sa.Column("answer_type", sa.String(length=30), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_triage_criteria_code", "triage_criteria", ["code"], unique=True)

    op.create_table(
        "triages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("evaluator_user_id", sa.Uuid(), nullable=False),
        sa.Column("classification_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("technical_opinion", sa.Text(), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("defects", sa.Text(), nullable=True),
        sa.Column("reusable_components", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('IN_PROGRESS', 'COMPLETED', 'CANCELLED')",
            name="ck_triages_status",
        ),
        sa.ForeignKeyConstraint(
            ["classification_id"],
            ["triage_classifications.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["evaluator_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_triages_equipment_id", "triages", ["equipment_id"])
    op.create_index("ix_triages_evaluator_user_id", "triages", ["evaluator_user_id"])
    op.create_index("ix_triages_classification_id", "triages", ["classification_id"])
    op.create_index("ix_triages_status", "triages", ["status"])
    op.create_index("ix_triages_started_at", "triages", ["started_at"])
    op.create_index("ix_triages_completed_at", "triages", ["completed_at"])
    op.create_index(
        "ix_triages_equipment_started",
        "triages",
        ["equipment_id", "started_at"],
    )
    op.create_index(
        "uq_triages_one_in_progress_per_equipment",
        "triages",
        ["equipment_id"],
        unique=True,
        postgresql_where=sa.text("status = 'IN_PROGRESS'"),
        sqlite_where=sa.text("status = 'IN_PROGRESS'"),
    )

    op.create_table(
        "triage_answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("triage_id", sa.Uuid(), nullable=False),
        sa.Column("criterion_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["criterion_id"], ["triage_criteria.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["triage_id"], ["triages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("triage_id", "criterion_id", name="uq_triage_answer_criterion"),
    )
    op.create_index("ix_triage_answers_triage_id", "triage_answers", ["triage_id"])
    op.create_index("ix_triage_answers_criterion_id", "triage_answers", ["criterion_id"])


def downgrade() -> None:
    op.drop_table("triage_answers")
    op.drop_table("triages")
    op.drop_table("triage_criteria")
    op.drop_table("triage_classifications")
