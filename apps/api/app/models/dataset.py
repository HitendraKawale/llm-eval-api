from typing import Any

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

class Dataset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")

    items: Mapped[list["DatasetItem"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="DatasetItem.row_index",
    )
 
 
class DatasetItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dataset_items"
    __table_args__ = (
        UniqueConstraint("dataset_id", "row_index", name="uq_dataset_items_dataset_row_index"),
    )

    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    dataset: Mapped["Dataset"] = relationship(back_populates="items")