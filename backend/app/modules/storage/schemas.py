import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StorageLocationCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    warehouse: str = Field(min_length=2, max_length=120)
    aisle: str | None = Field(default=None, max_length=50)
    rack: str | None = Field(default=None, max_length=50)
    shelf: str | None = Field(default=None, max_length=50)
    position: str | None = Field(default=None, max_length=50)
    capacity: int = Field(default=1, ge=1, le=10000)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class StorageLocationUpdate(BaseModel):
    warehouse: str | None = Field(default=None, min_length=2, max_length=120)
    aisle: str | None = Field(default=None, max_length=50)
    rack: str | None = Field(default=None, max_length=50)
    shelf: str | None = Field(default=None, max_length=50)
    position: str | None = Field(default=None, max_length=50)
    capacity: int | None = Field(default=None, ge=1, le=10000)
    notes: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class StorageLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    warehouse: str
    aisle: str | None
    rack: str | None
    shelf: str | None
    position: str | None
    capacity: int
    occupied: int
    available: int
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StorageMovementCreate(BaseModel):
    equipment_id: uuid.UUID
    to_location_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=500)
    occurred_at: datetime | None = None


class StorageOccupancyRead(BaseModel):
    assignment_id: uuid.UUID
    equipment_id: uuid.UUID
    tracking_code: str
    equipment_description: str
    current_status: str
    location: StorageLocationRead
    entered_at: datetime
    dwell_days: int
    alert: bool


class StorageMovementRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    tracking_code: str
    movement_type: str
    from_location_code: str | None
    to_location_code: str | None
    occurred_at: datetime
    user_id: uuid.UUID | None
    notes: str | None


class StorageDashboardRead(BaseModel):
    locations_total: int
    locations_active: int
    capacity_total: int
    occupied_total: int
    available_total: int
    dwell_alerts: int
