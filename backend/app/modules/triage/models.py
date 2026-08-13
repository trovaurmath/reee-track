import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.modules.equipment.models import Equipment
    from app.modules.identity.models import User


class TriageClassification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "triage_classifications"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    target_status: Mapped[str] = mapped_column(String(50), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TriageCriterion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "triage_criteria"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    question: Mapped[str] = mapped_column(String(255), nullable=False)
    help_text: Mapped[str | None] = mapped_column(String(255))
    answer_type: Mapped[str] = mapped_column(String(30), nullable=False)
    options_json: Mapped[list[str]] = mapped_column("options", JSON, default=list, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Triage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "triages"
    __table_args__ = (
        CheckConstraint(
            "status IN ('IN_PROGRESS', 'COMPLETED', 'CANCELLED')",
            name="ck_triages_status",
        ),
        Index("ix_triages_equipment_started", "equipment_id", "started_at"),
        Index(
            "uq_triages_one_in_progress_per_equipment",
            "equipment_id",
            unique=True,
            postgresql_where=text("status = 'IN_PROGRESS'"),
            sqlite_where=text("status = 'IN_PROGRESS'"),
        ),
    )

    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipments.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    evaluator_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    classification_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("triage_classifications.id", ondelete="RESTRICT"),
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="IN_PROGRESS",
        index=True,
        nullable=False,
    )
    technical_opinion: Mapped[str | None] = mapped_column(Text)
    observations: Mapped[str | None] = mapped_column(Text)
    defects: Mapped[str | None] = mapped_column(Text)
    reusable_components: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    equipment: Mapped["Equipment"] = relationship(back_populates="triages", lazy="joined")
    evaluator: Mapped["User"] = relationship(lazy="joined")
    classification: Mapped[TriageClassification | None] = relationship(lazy="joined")
    answers: Mapped[list["TriageAnswer"]] = relationship(
        back_populates="triage",
        cascade="all, delete-orphan",
        order_by="TriageAnswer.created_at",
        lazy="selectin",
    )


class TriageAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "triage_answers"
    __table_args__ = (
        UniqueConstraint("triage_id", "criterion_id", name="uq_triage_answer_criterion"),
    )

    triage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("triages.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    criterion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("triage_criteria.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    value_json: Mapped[object] = mapped_column("value", JSON, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    triage: Mapped[Triage] = relationship(back_populates="answers")
    criterion: Mapped[TriageCriterion] = relationship(lazy="joined")
