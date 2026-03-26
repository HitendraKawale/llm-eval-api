from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import PromptTemplate
from app.schemas import (
    PromptTemplateCreate,
    PromptTemplateRead,
    PromptTemplateUpdate,
)

router = APIRouter(prefix="/prompt-templates", tags=["prompt-templates"])


@router.post("", response_model=PromptTemplateRead, status_code=status.HTTP_201_CREATED)
def create_prompt_template(
    payload: PromptTemplateCreate,
    db: Session = Depends(get_db),
) -> PromptTemplate:
    existing = db.scalar(select(PromptTemplate).where(PromptTemplate.name == payload.name))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Prompt template with name '{payload.name}' already exists.",
        )

    prompt_template = PromptTemplate(
        name=payload.name,
        description=payload.description,
        template_text=payload.template_text,
        version=payload.version,
        input_variables=payload.input_variables,
        is_active=payload.is_active,
    )

    db.add(prompt_template)
    db.commit()
    db.refresh(prompt_template)
    return prompt_template


@router.get("", response_model=list[PromptTemplateRead])
def list_prompt_templates(db: Session = Depends(get_db)) -> list[PromptTemplate]:
    result = db.scalars(select(PromptTemplate).order_by(PromptTemplate.created_at.desc()))
    return list(result)


@router.get("/{prompt_template_id}", response_model=PromptTemplateRead)
def get_prompt_template(prompt_template_id: str, db: Session = Depends(get_db)) -> PromptTemplate:
    prompt_template = db.get(PromptTemplate, prompt_template_id)
    if not prompt_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found.",
        )
    return prompt_template


@router.patch("/{prompt_template_id}", response_model=PromptTemplateRead)
def update_prompt_template(
    prompt_template_id: str,
    payload: PromptTemplateUpdate,
    db: Session = Depends(get_db),
) -> PromptTemplate:
    prompt_template = db.get(PromptTemplate, prompt_template_id)
    if not prompt_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = db.scalar(
            select(PromptTemplate).where(
                PromptTemplate.name == update_data["name"],
                PromptTemplate.id != prompt_template_id,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Prompt template with name '{update_data['name']}' already exists.",
            )

    for field, value in update_data.items():
        setattr(prompt_template, field, value)

    db.add(prompt_template)
    db.commit()
    db.refresh(prompt_template)
    return prompt_template


@router.delete("/{prompt_template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt_template(
    prompt_template_id: str,
    db: Session = Depends(get_db),
) -> Response:
    prompt_template = db.get(PromptTemplate, prompt_template_id)
    if not prompt_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found.",
        )

    db.delete(prompt_template)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)