"""FastAPI application entry point."""

from typing import Any

import uvicorn
from fastapi import FastAPI

from ecommerce_catalog_service.api.categories import router as categories_router
from ecommerce_catalog_service.api.products import router as products_router
from ecommerce_catalog_service.config import get_settings


def health() -> dict[str, Any]:
    """Report the process health status."""
    settings = get_settings()
    return {"status": "ok", "version": settings.app_version}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    application.include_router(categories_router, prefix="/api/v1")
    application.include_router(products_router, prefix="/api/v1")

    application.add_api_route("/health", health, methods=["GET"], tags=["health"])

    return application


app = create_app()


def run() -> None:
    """Run the development server."""
    uvicorn.run(
        "ecommerce_catalog_service.main:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=True,
    )
