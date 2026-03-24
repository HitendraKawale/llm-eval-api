from enum import Enum

from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin 

class ProviderType(str, Enum):
    openai = "openai"
    ollama = "ollama"
    openai_compatible = "openai_compatibel"

class ModelConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "model_config"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_key_env_var: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_local: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_parameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)