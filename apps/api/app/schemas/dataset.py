from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    task_type: str = Field(default="general", min_length=1, max_length=50)
    version: int = Field(default=1, ge=1)
    source_type: str = Field(default="manual", min_length=1, max_length=20)


class DatasetItemCreate(BaseModel):
    row_index: int = Field(ge=0)
    input_text: str = Field(min_length=1)
    expected_output: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class DatasetItemRead(BaseModel):
    id: str
    dataset_id: str
    row_index: int
    input_text: str
    expected_output: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetRead(BaseModel):
    id: str
    name: str
    description: str | None
    task_type: str
    version: int
    source_type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetDetailRead(DatasetRead):
    items: list[DatasetItemRead] = Field(default_factory=list)