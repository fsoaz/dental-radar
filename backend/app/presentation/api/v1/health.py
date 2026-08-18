from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.presentation.api.deps import get_db_session

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@router.get("/health/live", response_model=HealthResponse)
def liveness_check() -> HealthResponse:
    """Process is running — used by orchestrator liveness probes."""
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check(
    request: Request, response: Response, db: Session = Depends(get_db_session)
) -> HealthResponse:
    """Database and Redis reachable — used before accepting traffic."""
    try:
        db.execute(text("SELECT 1"))
        await request.app.state.rate_limit_store.ping()
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="degraded")
    return HealthResponse(status="ok")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request, response: Response, db: Session = Depends(get_db_session)
) -> HealthResponse:
    """Backward-compatible readiness check."""
    try:
        db.execute(text("SELECT 1"))
        await request.app.state.rate_limit_store.ping()
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="degraded")
    return HealthResponse(status="ok")
