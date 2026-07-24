"""Drop clinic.services: never populated by any write path, always empty."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_drop_clinic_services"
down_revision = "0002_enrich_fingerprint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("clinic", "services")


def downgrade() -> None:
    op.add_column(
        "clinic",
        sa.Column(
            "services",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
