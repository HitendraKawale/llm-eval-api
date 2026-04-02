import csv
import io
import json

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Dataset, DatasetItem


def _read_uploaded_text_file(
    file: UploadFile, *, allowed_extensions: tuple[str, ...]
) -> str:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    if not file.filename.lower().endswith(allowed_extensions):
        allowed = ", ".join(allowed_extensions)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {allowed} files are supported for this endpoint.",
        )

    raw_bytes = file.file.read()
    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be valid UTF-8 text.",
        ) from exc


def _get_next_row_index(*, db: Session, dataset_id: str) -> int:
    next_row_index = db.scalar(
        select(func.coalesce(func.max(DatasetItem.row_index), -1) + 1).where(
            DatasetItem.dataset_id == dataset_id
        )
    )
    return 0 if next_row_index is None else next_row_index


def import_dataset_items_from_jsonl(
    *,
    db: Session,
    dataset: Dataset,
    file: UploadFile,
) -> list[DatasetItem]:
    content = _read_uploaded_text_file(file, allowed_extensions=(".jsonl",))

    lines = content.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded JSONL file contains no data rows.",
        )

    current_row_index = _get_next_row_index(db=db, dataset_id=dataset.id)
    items_to_create: list[DatasetItem] = []

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


def import_dataset_items_from_csv(
    *,
    db: Session,
    dataset: Dataset,
    file: UploadFile,
) -> list[DatasetItem]:
    content = _read_uploaded_text_file(file, allowed_extensions=(".csv",))

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded CSV file must include a header row.",
        )

    fieldnames = {name.strip() for name in reader.fieldnames if name}
    if "input" not in fieldnames and "input_text" not in fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must include an 'input' or 'input_text' column.",
        )

    current_row_index = _get_next_row_index(db=db, dataset_id=dataset.id)
    items_to_create: list[DatasetItem] = []

    for row_number, row in enumerate(reader, start=2):
        normalized_row = {
            (key.strip() if key else key): (
                value.strip() if isinstance(value, str) else value
            )
            for key, value in row.items()
        }

        input_text = normalized_row.get("input")
        if not input_text:
            input_text = normalized_row.get("input_text")

        if not isinstance(input_text, str) or not input_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CSV at row {row_number}: missing required string column 'input' or 'input_text'.",
            )

        expected_output = normalized_row.get("expected_output")
        if not expected_output:
            expected_output = normalized_row.get("expected")
        if expected_output == "":
            expected_output = None

        metadata_raw = normalized_row.get("metadata_json")
        if metadata_raw in (None, ""):
            metadata_json = {}
        else:
            try:
                metadata_json = json.loads(metadata_raw)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid CSV at row {row_number}: 'metadata_json' must be valid JSON. {exc.msg}.",
                ) from exc

            if not isinstance(metadata_json, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid CSV at row {row_number}: 'metadata_json' must decode to a JSON object.",
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
            detail="Uploaded CSV file contains no data rows.",
        )

    db.add_all(items_to_create)
    db.commit()

    for item in items_to_create:
        db.refresh(item)

    return items_to_create
