from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["Saúde"])


class HealthResponse(BaseModel):
    status: str
    database: str | None = None


@router.get("/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
def ready(session: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    session.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="available")

