import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CatalogCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class CatalogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None
    is_active: bool


class EquipmentCreate(BaseModel):
    asset_number: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=150)
    equipment_type_id: uuid.UUID
    category_id: uuid.UUID
    origin_sector_id: uuid.UUID
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=150)
    description: str | None = None
    initial_condition: str = Field(min_length=2, max_length=255)
    collection_date: datetime
    collection_notes: str | None = None


class EquipmentUpdate(BaseModel):
    asset_number: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=150)
    equipment_type_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    origin_sector_id: uuid.UUID | None = None
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    initial_condition: str | None = Field(default=None, min_length=2, max_length=255)
    collection_notes: str | None = None


class EquipmentRead(BaseModel):
    id: uuid.UUID
    tracking_code: str
    asset_number: str | None
    serial_number: str | None
    equipment_type: CatalogRead
    category: CatalogRead
    origin_sector: CatalogRead
    brand: str
    model: str
    description: str | None
    initial_condition: str
    current_status: str
    collection_date: datetime
    collection_notes: str | None
    is_archived: bool
    archived_at: datetime | None
    archive_reason: str | None
    created_at: datetime
    updated_at: datetime


class EquipmentListResponse(BaseModel):
    items: list[EquipmentRead]
    total: int
    limit: int
    offset: int


class EquipmentArchiveRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class EquipmentEventRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    event_type: str
    previous_status: str | None
    new_status: str | None
    timestamp: datetime
    user_id: uuid.UUID | None
    location: str | None
    description: str
    metadata: dict[str, object]


class WorkflowStatusRead(BaseModel):
    code: str
    label: str
    stage: str
    terminal: bool


class WorkflowTransitionRequest(BaseModel):
    new_status: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=5, max_length=500)
    location: str | None = Field(default=None, max_length=255)
    occurred_at: datetime | None = None

    @field_validator("new_status")
    @classmethod
    def normalize_status(cls, value: str) -> str:
        return value.strip().upper()


class TimelineNoteCreate(BaseModel):
    description: str = Field(min_length=5, max_length=500)
    location: str | None = Field(default=None, max_length=255)
    occurred_at: datetime | None = None


class TraceabilityEventRead(EquipmentEventRead):
    tracking_code: str
    equipment_description: str
    status_label: str | None


class TraceabilityFeedResponse(BaseModel):
    items: list[TraceabilityEventRead]
    total: int
    limit: int
    offset: int
