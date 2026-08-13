import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.modules.triage.models import Triage


class EquipmentCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "equipment_categories"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EquipmentType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "equipment_types"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Sector(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sectors"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class NumberSequence(Base):
    __tablename__ = "number_sequences"
    __table_args__ = (UniqueConstraint("namespace", "year", name="uq_number_sequence"),)

    namespace: Mapped[str] = mapped_column(String(50), primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    current_value: Mapped[int] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class Equipment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "equipments"
    __table_args__ = (
        Index("ix_equipments_brand_model", "brand", "model"),
    )

    tracking_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    asset_number: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    serial_number: Mapped[str | None] = mapped_column(String(150), index=True)
    equipment_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipment_types.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipment_categories.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    origin_sector_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sectors.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    brand: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    initial_condition: Mapped[str] = mapped_column(String(255), nullable=False)
    current_status: Mapped[str] = mapped_column(
        String(50),
        default="AGUARDANDO_TRIAGEM",
        index=True,
        nullable=False,
    )
    collection_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    archived_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    archive_reason: Mapped[str | None] = mapped_column(Text)

    equipment_type: Mapped[EquipmentType] = relationship(lazy="joined")
    category: Mapped[EquipmentCategory] = relationship(lazy="joined")
    origin_sector: Mapped[Sector] = relationship(lazy="joined")
    collection: Mapped["Collection"] = relationship(
        back_populates="equipment",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    events: Mapped[list["EquipmentEvent"]] = relationship(
        back_populates="equipment",
        order_by="EquipmentEvent.occurred_at",
    )
    triages: Mapped[list["Triage"]] = relationship(
        back_populates="equipment",
        order_by="Triage.started_at",
    )


class Collection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "collections"

    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipments.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    collector_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)

    equipment: Mapped[Equipment] = relationship(back_populates="collection")


class EquipmentEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "equipment_events"
    __table_args__ = (
        Index("ix_equipment_events_equipment_time", "equipment_id", "occurred_at"),
    )

    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipments.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(50))
    new_status: Mapped[str | None] = mapped_column(String(50))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    location: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSON,
        default=dict,
        nullable=False,
    )

    equipment: Mapped[Equipment] = relationship(back_populates="events")
