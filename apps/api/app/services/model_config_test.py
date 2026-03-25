from app.models import ModelConfig
from app.providers import get_provider_adapter
from app.providers.base import ProviderGenerateResult
from app.providers.openai import resolve_api_key_from_env


def test_model_config(
    *,
    model_config: ModelConfig,
    prompt: str,
    override_parameters: dict,
) -> ProviderGenerateResult:
    adapter = get_provider_adapter(model_config.provider)

    merged_parameters = {
        **(model_config.default_parameters or {}),
        **(override_parameters or {}),
    }

    api_key = resolve_api_key_from_env(model_config.api_key_env_var)

    return adapter.generate(
        prompt=prompt,
        model_name=model_config.model_name,
        base_url=model_config.base_url,
        api_key=api_key,
        parameters=merged_parameters,
        provider=model_config.provider,
    )