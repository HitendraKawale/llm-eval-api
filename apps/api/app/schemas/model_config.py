from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


_ALLOWED_PROVIDERS = {"openai", "ollama", "openai_compatible"}


class ModelConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider: str = Field(min_length=1, max_length=50)
    model_name: str = Field(min_length=1, max_length=100)
    base_url: str | None = None
    api_key_env_var: str | None = Field(default=None, max_length=100)
    is_active: bool = True
    is_local: bool = False
    default_parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        if value not in _ALLOWED_PROVIDERS:
            raise ValueError(f"provider must be one of: {', '.join(sorted(_ALLOWED_PROVIDERS))}")
        return value


class ModelConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    provider: str | None = Field(default=None, min_length=1, max_length=50)
    model_name: str | None = Field(default=None, min_length=1, max_length=100)
    base_url: str | None = None
    api_key_env_var: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    is_local: bool | None = None
    default_parameters: dict[str, Any] | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str | None) -> str | None:
        if value is not None and value not in _ALLOWED_PROVIDERS:
            raise ValueError(f"provider must be one of: {', '.join(sorted(_ALLOWED_PROVIDERS))}")
        return value


class ModelConfigRead(BaseModel):
    id: str
    name: str
    provider: str
    model_name: str
    base_url: str | None
    api_key_env_var: str | None
    is_active: bool
    is_local: bool
    default_parameters: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}