from pydantic import BaseModel, Field

from app.schemas.dataset import DatasetItemCreate, DatasetItemRead


class DatasetItemsBulkCreate(BaseModel):
    items: list[DatasetItemCreate] = Field(min_length=1)


class DatasetItemsBulkRead(BaseModel):
    created_count: int
    items: list[DatasetItemRead]
