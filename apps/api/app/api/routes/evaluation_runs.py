from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Dataset, EvaluationRun, ModelConfig, PromptTemplate
from app.schemas import EvaluationRunCreate, EvaluationRunDetailRead, EvaluationRunRead
from app.services.evaluation_runs import execute_evaluation_run

router = APIRouter(prefix="/evaluation-runs", tags=["evaluation-runs"])


@router.post("", response_model=EvaluationRunDetailRead, status_code=status.HTTP_201_CREATED)
def create_evaluation_run(
    payload: EvaluationRunCreate,
    db: Session = Depends(get_db),
) -> EvaluationRun:
    dataset = db.scalar(
        select(Dataset)
        .options(selectinload(Dataset.items))
        .where(Dataset.id == payload.dataset_id)
    )
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    prompt_template = db.get(PromptTemplate, payload.prompt_template_id)
    if not prompt_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found.",
        )

    model_config = db.get(ModelConfig, payload.model_config_id)
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model config not found.",
        )

    try:
        run = execute_evaluation_run(
            db=db,
            dataset=dataset,
            prompt_template=prompt_template,
            model_config=model_config,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return run


@router.get("", response_model=list[EvaluationRunRead])
def list_evaluation_runs(db: Session = Depends(get_db)) -> list[EvaluationRun]:
    result = db.scalars(
        select(EvaluationRun).order_by(EvaluationRun.created_at.desc())
    )
    return list(result)


@router.get("/{evaluation_run_id}", response_model=EvaluationRunDetailRead)
def get_evaluation_run(
    evaluation_run_id: str,
    db: Session = Depends(get_db),
) -> EvaluationRun:
    run = db.scalar(
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .where(EvaluationRun.id == evaluation_run_id)
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found.",
        )
    return run