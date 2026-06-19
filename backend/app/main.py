from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.domain.exceptions import ClinicNotFoundError, EnrichmentFailedError
from app.infrastructure.config.settings import settings
from app.infrastructure.logging_config import configure_logging
from app.presentation.api.v1 import clinics, health, scoring_config
from app.presentation.middleware.request_logging import RequestLoggingMiddleware


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Dental Radar API", version="0.1.0")

    app.add_middleware(RequestLoggingMiddleware)

    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(clinics.router, prefix="/api/v1")
    app.include_router(scoring_config.router, prefix="/api/v1")

    @app.exception_handler(ClinicNotFoundError)
    async def clinic_not_found_handler(_: Request, exc: ClinicNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "CLINIC_NOT_FOUND",
                    "message": str(exc),
                    "details": None,
                }
            },
        )

    @app.exception_handler(EnrichmentFailedError)
    async def enrichment_failed_handler(_: Request, exc: EnrichmentFailedError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": {
                    "code": "ENRICHMENT_FAILED",
                    "message": str(exc),
                    "details": None,
                }
            },
        )

    return app


app = create_app()
