import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions import (
    ApiKeyNotConfiguredError,
    ClinicNotFoundError,
    ClinicSourceError,
    EnrichmentFailedError,
    InvalidQueryError,
    RescoreJobNotFoundError,
    ScoringConfigConflictError,
    UnauthorizedError,
)
from app.infrastructure.config.settings import settings
from app.infrastructure.logging_config import configure_logging
from app.presentation.api.v1 import clinics, health, scoring_config
from app.presentation.middleware.rate_limit import RateLimitMiddleware, RedisRateLimitStore
from app.presentation.middleware.request_logging import RequestLoggingMiddleware

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def create_app() -> FastAPI:
    configure_logging()
    is_production = settings.app_env.lower().strip() == "production"
    api_key_configured = bool((settings.api_key or "").strip())
    if not api_key_configured:
        if settings.allow_unauthenticated:
            logger.warning(
                "API_KEY is unset and ALLOW_UNAUTHENTICATED=true — "
                "mutating/paid routes are OPEN. Never enable this outside local/test."
            )
        else:
            logger.error(
                "API_KEY is unset — mutating/paid routes will return 503 "
                "API_KEY_NOT_CONFIGURED. Set API_KEY, or ALLOW_UNAUTHENTICATED=true "
                "for local development only."
            )
    rate_limit_store = RedisRateLimitStore(settings.redis_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.rate_limit_store = rate_limit_store
        try:
            yield
        finally:
            await rate_limit_store.close()

    app = FastAPI(
        title="Dental Radar API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        store=rate_limit_store,
        limit=settings.rate_limit_per_minute,
        window_seconds=60,
        trusted_proxies=settings.rate_limit_trusted_proxies,
    )

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
            content=_error_body("CLINIC_NOT_FOUND", str(exc)),
        )

    @app.exception_handler(EnrichmentFailedError)
    async def enrichment_failed_handler(_: Request, exc: EnrichmentFailedError) -> JSONResponse:
        # exc.detail can contain raw upstream provider error bodies (status, url,
        # response text) — log it server-side only, never relay it to API clients.
        logger.error("Enrichment failed for clinic %s: %s", exc.clinic_id, exc.detail)
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=_error_body(
                "ENRICHMENT_FAILED",
                f"Enrichment failed for clinic {exc.clinic_id}. Please try again later.",
            ),
        )

    @app.exception_handler(ScoringConfigConflictError)
    async def scoring_config_conflict_handler(
        _: Request, exc: ScoringConfigConflictError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_error_body("SCORING_CONFIG_CONFLICT", str(exc)),
        )

    @app.exception_handler(ClinicSourceError)
    async def clinic_source_error_handler(_: Request, exc: ClinicSourceError) -> JSONResponse:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        if exc.code == "DISCOVERY_QUOTA_EXCEEDED":
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif exc.code == "DISCOVERY_UNAUTHORIZED":
            status_code = status.HTTP_502_BAD_GATEWAY
        return JSONResponse(
            status_code=status_code,
            content=_error_body(exc.code, exc.message),
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(_: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=_error_body("UNAUTHORIZED", exc.message),
            headers={"WWW-Authenticate": "ApiKey"},
        )

    @app.exception_handler(ApiKeyNotConfiguredError)
    async def api_key_not_configured_handler(
        _: Request, exc: ApiKeyNotConfiguredError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_body("API_KEY_NOT_CONFIGURED", str(exc)),
        )

    @app.exception_handler(InvalidQueryError)
    async def invalid_query_handler(_: Request, exc: InvalidQueryError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("VALIDATION_ERROR", exc.message),
        )

    @app.exception_handler(RescoreJobNotFoundError)
    async def rescore_job_not_found_handler(
        _: Request, exc: RescoreJobNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_error_body("RESCORE_JOB_NOT_FOUND", str(exc)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        safe_errors = jsonable_encoder(exc.errors(), custom_encoder={Exception: str})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                "VALIDATION_ERROR",
                "Request validation failed",
                details={"errors": safe_errors},
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, (HTTPException, StarletteHTTPException, RequestValidationError)):
            raise exc
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        logger.exception("Unhandled error request_id=%s path=%s", request_id, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                "INTERNAL_ERROR",
                "An unexpected error occurred",
                details={"request_id": request_id},
            ),
        )

    return app


app = create_app()
