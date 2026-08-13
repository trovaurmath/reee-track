from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.audit.router import router as audit_router
from app.modules.equipment.router import catalog_router, traceability_router
from app.modules.equipment.router import router as equipment_router
from app.modules.identity.router import router as identity_router
from app.modules.storage.router import router as storage_router
from app.modules.triage.router import configuration_router as triage_configuration_router
from app.modules.triage.router import equipment_router as equipment_triage_router
from app.modules.triage.router import router as triage_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(identity_router)
api_router.include_router(audit_router)
api_router.include_router(catalog_router)
api_router.include_router(equipment_router)
api_router.include_router(traceability_router)
api_router.include_router(storage_router)
api_router.include_router(triage_configuration_router)
api_router.include_router(triage_router)
api_router.include_router(equipment_triage_router)
