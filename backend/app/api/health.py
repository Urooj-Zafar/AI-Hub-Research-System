"""Basic app and liveness endpoints."""

from fastapi import APIRouter

from app.core.config import APP_DESCRIPTION, APP_NAME, APP_VERSION
from app.models.request_model import ApplicationInfo, HealthStatus

router = APIRouter()


@router.get("/", response_model=ApplicationInfo)
async def application_info() -> ApplicationInfo:
    return ApplicationInfo(
        name=APP_NAME,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
    )


@router.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/healthz", response_model=HealthStatus)
async def healthz() -> HealthStatus:
    return HealthStatus(status="ok")
