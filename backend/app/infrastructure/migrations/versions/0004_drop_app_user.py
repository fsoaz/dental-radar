"""Drop unused app_user authentication scaffolding."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_drop_app_user"
down_revision = "0003_drop_clinic_services"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("app_user")


def downgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="operator"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
