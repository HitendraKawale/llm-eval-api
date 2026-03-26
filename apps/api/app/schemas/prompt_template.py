from datetime import datetime

from pydantic import BaseModel, Field

class PromptTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    template_text: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    input_variables: list[str] = Field(default_factory=list)
    is_active: bool = True


class PromptTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    template_text: str | None = None
    version: int | None = Field(default=None, ge=1)
    input_variables: list[str] | None = None
    is_active: bool | None = None


class PromptTemplateRead(BaseModel):
    id: str
    name: str
    description: str | None
    template_text: str
    version: int
    input_variables: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}