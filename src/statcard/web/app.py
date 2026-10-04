"""FastAPI application factory for the statcard web backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from statcard import __version__
from statcard.web.api import router as api_router
from statcard.web.ratelimit import SlidingWindowLimiter
from statcard.web.settings import Settings, load_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app; settings are injectable for tests."""
    app = FastAPI(title="statcard", version=__version__, redoc_url=None)
    app.state.settings = settings or load_settings()
    app.state.limiter = SlidingWindowLimiter()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(app.state.settings.allowed_origins),
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["ops"])
    async def healthz() -> dict[str, str]:
        """Liveness probe for Railway healthchecks and the Plan-B pinger."""
        return {"status": "ok", "version": __version__}

    app.include_router(api_router)
    return app


app = create_app()
