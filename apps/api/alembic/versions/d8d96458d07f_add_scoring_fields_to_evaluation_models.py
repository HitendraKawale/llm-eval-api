"""add scoring fields to evaluation models

Revision ID: d8d96458d07f
Revises: a28c4231b43f
Create Date: 2026-03-29 14:15:48.032682

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d8d96458d07f"
down_revision: Union[str, Sequence[str], None] = "a28c4231b43f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("evaluation_results", sa.Column("score", sa.Float(), nullable=True))
    op.add_column(
        "evaluation_results", sa.Column("passed", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "evaluation_results",
        sa.Column("scoring_method", sa.String(length=50), nullable=True),
    )

    op.add_column(
        "evaluation_runs",
        sa.Column("passed_items", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("evaluation_runs", sa.Column("score_mean", sa.Float(), nullable=True))
    op.add_column("evaluation_runs", sa.Column("pass_rate", sa.Float(), nullable=True))

    op.alter_column("evaluation_runs", "passed_items", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("evaluation_runs", "pass_rate")
    op.drop_column("evaluation_runs", "score_mean")
    op.drop_column("evaluation_runs", "passed_items")
    op.drop_column("evaluation_results", "scoring_method")
    op.drop_column("evaluation_results", "passed")
    op.drop_column("evaluation_results", "score")
