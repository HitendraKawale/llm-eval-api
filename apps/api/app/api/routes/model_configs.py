from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ModelConfig
from app.schemas import ModelConfigCreate, ModelConfigRead

router = APIRouter(prefix="/model-configs", tags=["model-configs"])


@router.post("", response_model=ModelConfigRead, status_code=status.HTTP_201_CREATED)
def create_model_config(
    payload: ModelConfigCreate,
    db: Session = Depends(get_db),
) -> ModelConfig:
    existing = db.scalar(select(ModelConfig).where(ModelConfig.name == payload.name))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model config with name '{payload.name}' already exists.",
        )

    model_config = ModelConfig(
        name=payload.name,
        provider=payload.provider,
        model_name=payload.model_name,
        base_url=payload.base_url,
        api_key_env_var=payload.api_key_env_var,
        is_active=payload.is_active,
        is_local=payload.is_local,
        default_parameters=payload.default_parameters,
    )

    db.add(model_config)
    db.commit()
    db.refresh(model_config)
    return model_config


@router.get("", response_model=list[ModelConfigRead])
def list_model_configs(db: Session = Depends(get_db)) -> list[ModelConfig]:
    result = db.scalars(select(ModelConfig).order_by(ModelConfig.created_at.desc()))
    return list(result)


@router.get("/{model_config_id}", response_model=ModelConfigRead)
def get_model_config(model_config_id: str, db: Session = Depends(get_db)) -> ModelConfig:
    model_config = db.get(ModelConfig, model_config_id)
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model config not found.",
        )
    return model_config