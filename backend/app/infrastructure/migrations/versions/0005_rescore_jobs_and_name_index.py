"""Add durable rescore jobs and index-backed clinic-name ordering."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_rescore_jobs"
down_revision = "0004_drop_app_user"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_clinic_name_id", "clinic", ["name", "id"], unique=False)
    op.create_table(
        "rescore_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("config_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rescored", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_rescore_job_status",
        ),
        sa.ForeignKeyConstraint(["config_version"], ["scoring_config.version"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rescore_job_status_created",
        "rescore_job",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rescore_job_status_created", table_name="rescore_job")
    op.drop_table("rescore_job")
    op.drop_index("ix_clinic_name_id", table_name="clinic")
