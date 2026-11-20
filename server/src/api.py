"""Local application shell. No business records are exposed."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.trustedhost import TrustedHostMiddleware


class Health(BaseModel):
    status: Literal["ok"] = "ok"


def create_app() -> FastAPI:
    application = FastAPI(title="YggdrasilCRM API", docs_url=None, redoc_url=None)
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1"],
    )

    @application.get("/api/health")
    def health() -> Health:
        """Check API liveness without checking infrastructure."""
        return Health()

    return application


app = create_app()
