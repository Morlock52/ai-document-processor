from fastapi import APIRouter

from app.api.endpoints import documents, health, schemas

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(schemas.router, prefix="/schemas", tags=["schemas"])