import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class StorageLocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "storage_locations"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    warehouse: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    aisle: Mapped[str | None] = mapped_column(String(50))
    rack: Mapped[str | None] = mapped_column(String(50))
    shelf: Mapped[str | None] = mapped_column(String(50))
    position: Mapped[str | None] = mapped_column(String(50))
    capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StorageAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "storage_assignments"

    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipments.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
        nullable=False,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("storage_locations.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True, nullable=False
    )


class StorageMovement(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "storage_movements"
    __table_args__ = (
        Index("ix_storage_movements_equipment_time", "equipment_id", "occurred_at"),
    )

    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipments.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    from_location_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("storage_locations.id", ondelete="RESTRICT"), index=True
    )
    to_location_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("storage_locations.id", ondelete="RESTRICT"), index=True
    )
    movement_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)
