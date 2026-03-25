import os
from time import perf_counter
from typing import Any

import httpx

from app.providers.base import BaseProviderAdapter, ProviderGenerateResult


class OpenAIAdapter(BaseProviderAdapter):
    def generate(
        self,
        *,
        prompt: str,
        model_name: str,
        base_url: str | None,
        api_key: str | None,
        parameters: dict[str, Any],
        provider: str,
    ) -> ProviderGenerateResult:
        resolved_api_key = api_key
        if not resolved_api_key:
            raise ValueError("OpenAI API key could not be resolved from environment.")

        api_base = (base_url or "https://api.openai.com/v1").rstrip("/")
        url = f"{api_base}/chat/completions"

        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            **(parameters or {}),
        }

        headers = {
            "Authorization": f"Bearer {resolved_api_key}",
            "Content-Type": "application/json",
        }

        start = perf_counter()
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        latency_ms = int((perf_counter() - start) * 1000)

        output_text = ""
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            output_text = message.get("content", "") or ""

        return ProviderGenerateResult(
            provider=provider,
            model_name=model_name,
            output_text=output_text,
            latency_ms=latency_ms,
            raw_response=data,
            usage=data.get("usage"),
        )


def resolve_api_key_from_env(env_var_name: str | None) -> str | None:
    if not env_var_name:
        return None
    return os.getenv(env_var_name)