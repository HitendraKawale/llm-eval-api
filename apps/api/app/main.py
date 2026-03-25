from fastapi import FastAPI

from app.api.routes import model_configs_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)


@app.get("/health")
def health_check() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "api",
        "environment": settings.app_env,
        "debug": settings.debug,
    }


app.include_router(model_configs_router, prefix=settings.api_v1_prefix)