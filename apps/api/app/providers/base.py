from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderGenerateResult:
    provider: str
    model_name: str
    output_text: str
    latency_ms: int
    raw_response: dict[str, Any]
    usage: dict[str, Any] | None = None


class BaseProviderAdapter(ABC):
    @abstractmethod
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
        raise NotImplementedError