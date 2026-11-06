"""FastAPI application entry point."""

from fastapi import FastAPI

from job_agent.api.routes import router as api_router
from job_agent.core.config import get_settings


def create_app() -> FastAPI:
    """Create the API application."""

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        """Liveness check. Database readiness is added when persistence is implemented."""

        return {"status": "ok", "environment": settings.app_env}

    return app


app = create_app()
