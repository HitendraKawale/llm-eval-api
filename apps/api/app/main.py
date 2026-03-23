from fastapi import FastAPI

#local imports
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="LLM Evaluation Platform API",
    version="0.1.0",
    debug=settings.debug,
)


@app.get("/health")
def health_check() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "api",
        "envvironment": settings.app_env,
        "debug": settings.debug,
    }
