from fastapi import APIRouter
from app.api.endpoints import upload, filters, streaming

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(filters.router, prefix="/filters", tags=["filters"])
api_router.include_router(streaming.router, prefix="/stream", tags=["streaming"])