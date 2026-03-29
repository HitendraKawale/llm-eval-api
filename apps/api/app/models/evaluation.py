from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EvaluationRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_runs"

    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )
    prompt_template_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_templates.id"),
        nullable=False,
        index=True,
    )
    model_config_id: Mapped[str] = mapped_column(
        ForeignKey("model_configs.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    passed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    pass_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    dataset: Mapped["Dataset"] = relationship()
    prompt_template: Mapped["PromptTemplate"] = relationship()
    model_config: Mapped["ModelConfig"] = relationship()

    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="evaluation_run",
        cascade="all, delete-orphan",
        order_by="EvaluationResult.row_index",
    )


class EvaluationResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_results"

    evaluation_run_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_item_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_items.id"),
        nullable=False,
        index=True,
    )

    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")

    input_text_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)

    rendered_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_response: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    usage_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    scoring_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="results")
    dataset_item: Mapped["DatasetItem"] = relationship()
