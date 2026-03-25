from time import perf_counter
from typing import Any

import httpx

from app.providers.base import BaseProviderAdapter, ProviderGenerateResult


class OllamaAdapter(BaseProviderAdapter):
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
        if not base_url:
            base_url = "http://localhost:11434"

        url = f"{base_url.rstrip('/')}/api/generate"

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": parameters or {},
        }

        start = perf_counter()
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        latency_ms = int((perf_counter() - start) * 1000)

        return ProviderGenerateResult(
            provider=provider,
            model_name=model_name,
            output_text=data.get("response", ""),
            latency_ms=latency_ms,
            raw_response=data,
            usage={
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
            },
        )