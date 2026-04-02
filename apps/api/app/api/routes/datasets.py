from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Dataset, DatasetItem
from app.schemas import (
    DatasetCreate,
    DatasetDetailRead,
    DatasetItemCreate,
    DatasetItemRead,
    DatasetItemsBulkCreate,
    DatasetItemsBulkRead,
    DatasetJsonlImportRead,
    DatasetCSVImportRead,
    DatasetRead,
)
from app.services.dataset_import import (
    import_dataset_items_from_jsonl,
    import_dataset_items_from_csv,
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


@router.post(
    "/{dataset_id}/items",
    response_model=DatasetItemRead,
    status_code=status.HTTP_201_CREATED,
)
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


@router.post(
    "/{dataset_id}/items/bulk",
    response_model=DatasetItemsBulkRead,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset_items_bulk(
    dataset_id: str,
    payload: DatasetItemsBulkCreate,
    db: Session = Depends(get_db),
) -> DatasetItemsBulkRead:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    row_indexes = [item.row_index for item in payload.items]
    if len(row_indexes) != len(set(row_indexes)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate row_index values found in request payload.",
        )

    existing_row_indexes = set(
        db.scalars(
            select(DatasetItem.row_index).where(
                DatasetItem.dataset_id == dataset_id,
                DatasetItem.row_index.in_(row_indexes),
            )
        ).all()
    )
    if existing_row_indexes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Row indexes already exist for this dataset: {sorted(existing_row_indexes)}",
        )

    items: list[DatasetItem] = []
    for payload_item in payload.items:
        items.append(
            DatasetItem(
                dataset_id=dataset_id,
                row_index=payload_item.row_index,
                input_text=payload_item.input_text,
                expected_output=payload_item.expected_output,
                metadata_json=payload_item.metadata_json,
            )
        )

    db.add_all(items)
    db.commit()

    for item in items:
        db.refresh(item)

    return DatasetItemsBulkRead(
        created_count=len(items),
        items=items,
    )


@router.post(
    "/{dataset_id}/import/jsonl",
    response_model=DatasetJsonlImportRead,
    status_code=status.HTTP_201_CREATED,
)
def import_dataset_jsonl(
    dataset_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
) -> DatasetJsonlImportRead:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    items = import_dataset_items_from_jsonl(
        db=db,
        dataset=dataset,
        file=file,
    )

    return DatasetJsonlImportRead(
        dataset_id=dataset.id,
        created_count=len(items),
        starting_row_index=items[0].row_index if items else None,
        ending_row_index=items[-1].row_index if items else None,
    )


@router.post(
    "/{dataset_id}/import/csv",
    response_model=DatasetCSVImportRead,
    status_code=status.HTTP_201_CREATED,
)
def import_dataset_csv(
    dataset_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
) -> DatasetCSVImportRead:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    items = import_dataset_items_from_csv(
        db=db,
        dataset=dataset,
        file=file,
    )

    return DatasetCSVImportRead(
        dataset_id=dataset.id,
        created_count=len(items),
        starting_row_index=items[0].row_index if items else None,
        ending_row_index=items[-1].row_index if items else None,
    )
