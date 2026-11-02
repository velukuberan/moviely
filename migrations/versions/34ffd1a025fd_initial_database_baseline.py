"""initial database baseline

Revision ID: 34ffd1a025fd
Revises:
Create Date: 2026-11-02 17:20:03.966339

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "34ffd1a025fd"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
