from pydantic import BaseModel, ConfigDict


class DatasetJsonlImportRead(BaseModel):
    dataset_id: str
    created_count: int
    starting_row_index: int | None
    ending_row_index: int | None

    model_config = ConfigDict(from_attributes=True)


class DatasetCSVImportRead(BaseModel):
    dataset_id: str
    created_count: int
    starting_row_index: int | None
    ending_row_index: int | None

    model_config = ConfigDict(from_attributes=True)
