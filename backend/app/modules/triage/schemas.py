import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AnswerType = Literal["BOOLEAN", "TEXT", "NUMBER", "SINGLE_CHOICE", "MULTIPLE_CHOICE"]
AnswerValue = bool | str | float | list[str]


class ClassificationCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    target_status: str = Field(min_length=2, max_length=50)
    display_order: int = Field(default=0, ge=0, le=10_000)

    @field_validator("code", "target_status")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        return value.strip().upper()


class ClassificationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    target_status: str | None = Field(default=None, min_length=2, max_length=50)
    display_order: int | None = Field(default=None, ge=0, le=10_000)
    is_active: bool | None = None

    @field_validator("target_status")
    @classmethod
    def normalize_target_status(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value


class ClassificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None
    target_status: str
    display_order: int
    is_active: bool


class CriterionCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    question: str = Field(min_length=3, max_length=255)
    help_text: str | None = Field(default=None, max_length=255)
    answer_type: AnswerType
    options: list[str] = Field(default_factory=list, max_length=30)
    is_required: bool = True
    display_order: int = Field(default=0, ge=0, le=10_000)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_options(self) -> "CriterionCreate":
        if self.answer_type in {"SINGLE_CHOICE", "MULTIPLE_CHOICE"} and len(self.options) < 2:
            raise ValueError("Critérios de escolha precisam de pelo menos duas opções")
        if self.answer_type not in {"SINGLE_CHOICE", "MULTIPLE_CHOICE"} and self.options:
            raise ValueError("Este tipo de resposta não aceita opções")
        return self


class CriterionUpdate(BaseModel):
    question: str | None = Field(default=None, min_length=3, max_length=255)
    help_text: str | None = Field(default=None, max_length=255)
    answer_type: AnswerType | None = None
    options: list[str] | None = Field(default=None, max_length=30)
    is_required: bool | None = None
    display_order: int | None = Field(default=None, ge=0, le=10_000)
    is_active: bool | None = None


class CriterionRead(BaseModel):
    id: uuid.UUID
    code: str
    question: str
    help_text: str | None
    answer_type: str
    options: list[str]
    is_required: bool
    display_order: int
    is_active: bool


class TriageAnswerWrite(BaseModel):
    criterion_id: uuid.UUID
    value: AnswerValue
    notes: str | None = Field(default=None, max_length=2_000)


class TriageAnswersUpdate(BaseModel):
    answers: list[TriageAnswerWrite] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def reject_duplicates(self) -> "TriageAnswersUpdate":
        criterion_ids = [answer.criterion_id for answer in self.answers]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("Cada critério pode ser respondido apenas uma vez")
        return self


class TriageComplete(BaseModel):
    classification_id: uuid.UUID
    technical_opinion: str = Field(min_length=3, max_length=10_000)
    observations: str | None = Field(default=None, max_length=10_000)
    defects: str | None = Field(default=None, max_length=10_000)
    reusable_components: str | None = Field(default=None, max_length=10_000)


class TriageAnswerRead(BaseModel):
    id: uuid.UUID
    criterion_id: uuid.UUID
    criterion_code: str
    question: str
    answer_type: str
    value: AnswerValue
    notes: str | None


class TriageRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    tracking_code: str
    equipment_description: str
    evaluator_user_id: uuid.UUID
    evaluator_name: str
    status: str
    classification: ClassificationRead | None
    technical_opinion: str | None
    observations: str | None
    defects: str | None
    reusable_components: str | None
    started_at: datetime
    completed_at: datetime | None
    answers: list[TriageAnswerRead]


class TriageQueueItem(BaseModel):
    equipment_id: uuid.UUID
    tracking_code: str
    asset_number: str | None
    equipment_description: str
    category_name: str
    origin_sector_name: str
    current_status: str
    collection_date: datetime
    active_triage_id: uuid.UUID | None
    evaluator_name: str | None


class TriageQueueResponse(BaseModel):
    items: list[TriageQueueItem]
    total: int
