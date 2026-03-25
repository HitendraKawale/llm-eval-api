from typing import Any

from pydantic import BaseModel, Field


class ModelConfigTestRequest(BaseModel):
    prompt: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ModelConfigTestResponse(BaseModel):
    provider: str
    model_name: str
    output_text: str
    latency_ms: int
    raw_response: dict[str, Any]
    usage: dict[str, Any] | None = None