from app.api.routes.datasets import router as datasets_router
from app.api.routes.evaluation_runs import router as evaluation_runs_router
from app.api.routes.model_configs import router as model_configs_router
from app.api.routes.prompt_templates import router as prompt_templates_router

__all__ = ["datasets_router", "model_configs_router", "prompt_templates_router", "evaluation_runs_router"]