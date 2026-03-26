from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ModelConfig
from app.schemas import (
    ModelConfigCreate,
    ModelConfigRead,
    ModelConfigTestRequest,
    ModelConfigTestResponse,
    ModelConfigUpdate,
)
from app.services.model_config_test import test_model_config

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


@router.patch("/{model_config_id}", response_model=ModelConfigRead)
def update_model_config(
    model_config_id: str,
    payload: ModelConfigUpdate,
    db: Session = Depends(get_db),
) -> ModelConfig:
    model_config = db.get(ModelConfig, model_config_id)
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model config not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = db.scalar(
            select(ModelConfig).where(
                ModelConfig.name == update_data["name"],
                ModelConfig.id != model_config_id,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model config with name '{update_data['name']}' already exists.",
            )

    for field, value in update_data.items():
        setattr(model_config, field, value)

    db.add(model_config)
    db.commit()
    db.refresh(model_config)
    return model_config


@router.delete("/{model_config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_config(
    model_config_id: str,
    db: Session = Depends(get_db),
) -> Response:
    model_config = db.get(ModelConfig, model_config_id)
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model config not found.",
        )

    db.delete(model_config)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{model_config_id}/test", response_model=ModelConfigTestResponse)
def test_saved_model_config(
    model_config_id: str,
    payload: ModelConfigTestRequest,
    db: Session = Depends(get_db),
) -> ModelConfigTestResponse:
    model_config = db.get(ModelConfig, model_config_id)
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model config not found.",
        )

    try:
        result = test_model_config(
            model_config=model_config,
            prompt=payload.prompt,
            override_parameters=payload.parameters,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ModelConfigTestResponse(
        provider=result.provider,
        model_name=result.model_name,
        output_text=result.output_text,
        latency_ms=result.latency_ms,
        raw_response=result.raw_response,
        usage=result.usage,
    )