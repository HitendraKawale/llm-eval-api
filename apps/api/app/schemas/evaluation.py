from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvaluationRunCreate(BaseModel):
    dataset_id: str = Field(min_length=1)
    prompt_template_id: str = Field(min_length=1)
    model_config_id: str = Field(min_length=1)


class EvaluationResultRead(BaseModel):
    id: str
    evaluation_run_id: str
    dataset_item_id: str
    row_index: int
    status: str
    input_text_snapshot: str
    expected_output_snapshot: str | None
    rendered_prompt: str
    output_text: str | None
    raw_response: dict[str, Any]
    usage_json: dict[str, Any]
    latency_ms: int | None
    error_message: str | None
    score: float | None
    passed: bool | None
    scoring_method: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvaluationRunRead(BaseModel):
    id: str
    dataset_id: str
    prompt_template_id: str
    model_config_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    total_items: int
    completed_items: int
    failed_items: int
    passed_items: int
    score_mean: float | None
    pass_rate: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvaluationRunDetailRead(EvaluationRunRead):
    results: list[EvaluationResultRead] = Field(default_factory=list)
