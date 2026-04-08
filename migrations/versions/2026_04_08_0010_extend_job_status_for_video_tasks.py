"""
Extend job_status enum for staged and canceled video task states.

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2026-04-08 00:10:00

"""

from typing import Union

from alembic import op

# Revision identifiers
revision: str = "000000000003"
down_revision: Union[str, None] = "000000000002"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Add staged and canceled values to the job_status enum."""
    op.execute("ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'staged';")
    op.execute("ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'canceled';")


def downgrade() -> None:
    """Recreate the enum without staged/canceled, remapping terminal rows safely."""
    op.execute(
        """
        UPDATE analysis_job
        SET status = 'failed'
        WHERE status = 'canceled';
        """
    )
    op.execute(
        """
        UPDATE analysis_job
        SET status = 'pending'
        WHERE status = 'staged';
        """
    )
    op.execute("ALTER TYPE job_status RENAME TO job_status_old;")
    op.execute(
        """
        CREATE TYPE job_status AS ENUM (
            'pending', 'processing', 'completed', 'failed'
        );
        """
    )
    op.execute(
        """
        ALTER TABLE analysis_job
        ALTER COLUMN status TYPE job_status
        USING status::text::job_status;
        """
    )
    op.execute("DROP TYPE job_status_old;")
