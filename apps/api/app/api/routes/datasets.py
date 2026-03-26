from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Dataset, DatasetItem
from app.schemas import (
    DatasetCreate,
    DatasetDetailRead,
    DatasetItemCreate,
    DatasetItemRead,
    DatasetRead,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: DatasetCreate,
    db: Session = Depends(get_db),
) -> Dataset:
    existing = db.scalar(select(Dataset).where(Dataset.name == payload.name))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dataset with name '{payload.name}' already exists.",
        )

    dataset = Dataset(
        name=payload.name,
        description=payload.description,
        task_type=payload.task_type,
        version=payload.version,
        source_type=payload.source_type,
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("", response_model=list[DatasetRead])
def list_datasets(db: Session = Depends(get_db)) -> list[Dataset]:
    result = db.scalars(select(Dataset).order_by(Dataset.created_at.desc()))
    return list(result)


@router.get("/{dataset_id}", response_model=DatasetDetailRead)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> Dataset:
    dataset = db.scalar(
        select(Dataset)
        .options(selectinload(Dataset.items))
        .where(Dataset.id == dataset_id)
    )
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )
    return dataset


@router.post("/{dataset_id}/items", response_model=DatasetItemRead, status_code=status.HTTP_201_CREATED)
def create_dataset_item(
    dataset_id: str,
    payload: DatasetItemCreate,
    db: Session = Depends(get_db),
) -> DatasetItem:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    existing = db.scalar(
        select(DatasetItem).where(
            DatasetItem.dataset_id == dataset_id,
            DatasetItem.row_index == payload.row_index,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dataset item with row_index '{payload.row_index}' already exists for this dataset.",
        )

    item = DatasetItem(
        dataset_id=dataset_id,
        row_index=payload.row_index,
        input_text=payload.input_text,
        expected_output=payload.expected_output,
        metadata_json=payload.metadata_json,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    return item