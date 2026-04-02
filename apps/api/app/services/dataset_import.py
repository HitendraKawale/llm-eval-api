import json
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Dataset, DatasetItem


def import_dataset_items_from_jsonl(
    *,
    db: Session,
    dataset: Dataset,
    file: UploadFile,
) -> list[DatasetItem]:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    if not file.filename.lower().endswith(".jsonl"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .jsonl files are supported for this endpoint.",
        )

    raw_bytes = file.file.read()
    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be valid UTF-8 text.",
        ) from exc

    lines = content.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded JSONL file contains no data rows.",
        )

    next_row_index = db.scalar(
        select(func.coalesce(func.max(DatasetItem.row_index), -1) + 1).where(
            DatasetItem.dataset_id == dataset.id
        )
    )
    if next_row_index is None:
        next_row_index = 0

    items_to_create: list[DatasetItem] = []
    current_row_index = next_row_index

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSONL at line {line_number}: {exc.msg}.",
            ) from exc

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSONL at line {line_number}: each line must be a JSON object.",
            )

        input_text = payload.get("input")
        if input_text is None:
            input_text = payload.get("input_text")

        if not isinstance(input_text, str) or not input_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSONL at line {line_number}: missing required string field 'input' or 'input_text'.",
            )

        expected_output = payload.get("expected_output")
        if expected_output is None and "expected" in payload:
            expected_output = payload.get("expected")

        if expected_output is not None and not isinstance(expected_output, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSONL at line {line_number}: 'expected_output' must be a string or null.",
            )

        metadata_json = payload.get("metadata")
        if metadata_json is None and "metadata_json" in payload:
            metadata_json = payload.get("metadata_json")

        if metadata_json is None:
            metadata_json = {}

        if not isinstance(metadata_json, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSONL at line {line_number}: 'metadata' must be an object if provided.",
            )

        items_to_create.append(
            DatasetItem(
                dataset_id=dataset.id,
                row_index=current_row_index,
                input_text=input_text,
                expected_output=expected_output,
                metadata_json=metadata_json,
            )
        )
        current_row_index += 1

    if not items_to_create:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded JSONL file contains no valid data rows.",
        )

    db.add_all(items_to_create)
    db.commit()

    for item in items_to_create:
        db.refresh(item)

    return items_to_create
