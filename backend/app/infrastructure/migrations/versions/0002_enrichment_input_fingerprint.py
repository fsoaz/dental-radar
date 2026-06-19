"""Add input_fingerprint to enrichment for cache invalidation."""

import sqlalchemy as sa
from alembic import op

revision = "0002_enrich_fingerprint"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("enrichment", sa.Column("input_fingerprint", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("enrichment", "input_fingerprint")
