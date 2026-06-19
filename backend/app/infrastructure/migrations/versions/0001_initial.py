"""Initial schema and scoring_config seed."""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCORING_DEFAULTS = {
    "version": 1,
    "active": True,
    "weights": {
        "HIRING": 25,
        "ADVERTISING": 30,
        "WEBSITE_QUALITY": 15,
        "MULTI_LOCATION": 40,
        "HIGH_TICKET": 20,
    },
    "bands": [
        {"name": "COLD", "min": 0, "max": 50},
        {"name": "WARM", "min": 51, "max": 100},
        {"name": "HOT", "min": 101, "max": 150},
        {"name": "IMMEDIATE", "min": 151, "max": None},
    ],
}


def upgrade() -> None:
    op.create_table(
        "clinic",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("place_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("google_rating", sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column("google_review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locations_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "services", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"
        ),
        sa.Column(
            "social_urls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("place_id"),
    )
    op.create_table(
        "scoring_config",
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("weights", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("bands", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("version"),
    )
    op.create_index(
        "uq_scoring_config_active",
        "scoring_config",
        ["active"],
        unique=True,
        postgresql_where=sa.text("active"),
    )
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
    op.create_table(
        "location",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("street", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("postal_code", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("lat", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("lng", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinic.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_location_clinic", "location", ["clinic_id"], unique=False)
    op.create_index("ix_location_state_city", "location", ["state", "city"], unique=False)
    op.create_table(
        "signal",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("applied_weight", sa.Integer(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column(
            "confidence", sa.Numeric(precision=3, scale=2), nullable=False, server_default="1.0"
        ),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinic.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signal_clinic", "signal", ["clinic_id"], unique=False)
    op.create_index("uq_signal_clinic_type", "signal", ["clinic_id", "type"], unique=True)
    op.create_table(
        "score",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("config_version", sa.Integer(), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinic.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["config_version"], ["scoring_config.version"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id"),
    )
    op.create_index("ix_score_total", "score", [sa.text("total DESC")], unique=False)
    op.create_index("ix_score_priority", "score", ["priority"], unique=False)
    op.create_table(
        "enrichment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("growth_probability", sa.Integer(), nullable=True),
        sa.Column("technology_maturity", sa.Integer(), nullable=True),
        sa.Column("marketing_sophistication", sa.Integer(), nullable=True),
        sa.Column("expansion_probability", sa.Integer(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("provider", sa.Text(), nullable=True),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinic.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id"),
    )

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO scoring_config (version, active, weights, bands)
            VALUES (:version, :active, CAST(:weights AS jsonb), CAST(:bands AS jsonb))
            """
        ),
        {
            "version": SCORING_DEFAULTS["version"],
            "active": SCORING_DEFAULTS["active"],
            "weights": json.dumps(SCORING_DEFAULTS["weights"]),
            "bands": json.dumps(SCORING_DEFAULTS["bands"]),
        },
    )


def downgrade() -> None:
    op.drop_table("enrichment")
    op.drop_index("ix_score_priority", table_name="score")
    op.drop_index("ix_score_total", table_name="score")
    op.drop_table("score")
    op.drop_index("uq_signal_clinic_type", table_name="signal")
    op.drop_index("ix_signal_clinic", table_name="signal")
    op.drop_table("signal")
    op.drop_index("ix_location_state_city", table_name="location")
    op.drop_index("ix_location_clinic", table_name="location")
    op.drop_table("location")
    op.drop_table("app_user")
    op.drop_index("uq_scoring_config_active", table_name="scoring_config")
    op.drop_table("scoring_config")
    op.drop_table("clinic")
