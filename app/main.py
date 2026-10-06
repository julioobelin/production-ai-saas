"""Application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.ai.factory import build_chat_provider
from app.api.router import api_router
from app.api.routes.health import RequestLoggingMiddleware
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.db.vector_schema import assert_configured_dimensions

logger = logging.getLogger("app")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    assert_configured_dimensions(settings.embedding_dimensions)
    chat = build_chat_provider(settings)
    app = FastAPI(
        title="Production AI SaaS Backend",
        summary="Multi-tenant knowledge assistant API",
        version="0.1.0",
        description=(
            "Organizations store documents in knowledge bases and ask questions. "
            "Answers are grounded in retrieved passages. Lexical PostgreSQL search is "
            "the default. Vector search runs only when RETRIEVAL_MODE=vector."
        ),
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.include_router(health_router)
    app.include_router(api_router)
    logger.info(
        "application_start",
        extra={
            "event": "application_start",
            "retrieval_mode": settings.retrieval_mode,
            "provider": chat.name,
        },
    )
    return app


def _app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    error = exc if isinstance(exc, AppError) else AppError("internal_error", "Request failed", 500)
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
    )


def _validation_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": []},
        )
    errors = []
    for item in exc.errors():
        errors.append({key: value for key, value in item.items() if key not in {"input", "ctx"}})
    return JSONResponse(status_code=422, content=jsonable_encoder(errors))


app = create_app()
