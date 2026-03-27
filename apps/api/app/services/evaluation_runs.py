from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Dataset, EvaluationResult, EvaluationRun, ModelConfig, PromptTemplate
from app.services.model_config_test import test_model_config
from app.services.prompt_rendering import render_prompt_template


def execute_evaluation_run(
    *,
    db: Session,
    dataset: Dataset,
    prompt_template: PromptTemplate,
    model_config: ModelConfig,
) -> EvaluationRun:
    if not dataset.items:
        raise ValueError("Dataset has no items.")

    if not prompt_template.is_active:
        raise ValueError("Prompt template is inactive.")

    if not model_config.is_active:
        raise ValueError("Model config is inactive.")

    now = datetime.now(timezone.utc)

    run = EvaluationRun(
        dataset_id=dataset.id,
        prompt_template_id=prompt_template.id,
        model_config_id=model_config.id,
        status="running",
        started_at=now,
        total_items=len(dataset.items),
        completed_items=0,
        failed_items=0,
    )

    db.add(run)
    db.flush()

    for item in dataset.items:
        rendered_prompt = ""

        try:
            rendered_prompt = render_prompt_template(
                template_text=prompt_template.template_text,
                input_text=item.input_text,
                expected_output=item.expected_output,
                metadata_json=item.metadata_json,
                input_variables=prompt_template.input_variables,
            )

            provider_result = test_model_config(
                model_config=model_config,
                prompt=rendered_prompt,
                override_parameters={},
            )

            result = EvaluationResult(
                evaluation_run_id=run.id,
                dataset_item_id=item.id,
                row_index=item.row_index,
                status="success",
                input_text_snapshot=item.input_text,
                expected_output_snapshot=item.expected_output,
                rendered_prompt=rendered_prompt,
                output_text=provider_result.output_text,
                raw_response=provider_result.raw_response,
                usage_json=provider_result.usage or {},
                latency_ms=provider_result.latency_ms,
                error_message=None,
            )
            run.completed_items += 1

        except Exception as exc:
            result = EvaluationResult(
                evaluation_run_id=run.id,
                dataset_item_id=item.id,
                row_index=item.row_index,
                status="failed",
                input_text_snapshot=item.input_text,
                expected_output_snapshot=item.expected_output,
                rendered_prompt=rendered_prompt,
                output_text=None,
                raw_response={},
                usage_json={},
                latency_ms=None,
                error_message=str(exc),
            )
            run.failed_items += 1

        db.add(result)

    run.status = "completed" if run.failed_items == 0 else "completed_with_errors"
    run.completed_at = datetime.now(timezone.utc)

    db.add(run)
    db.commit()

    refreshed_run = db.scalar(
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .where(EvaluationRun.id == run.id)
    )
    if refreshed_run is None:
        raise ValueError("Failed to load created evaluation run.")

    return refreshed_run