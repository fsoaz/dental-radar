import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ClinicModel(Base):
    __tablename__ = "clinic"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    place_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    google_rating: Mapped[float | None] = mapped_column(Numeric(2, 1))
    google_review_count: Mapped[int] = mapped_column(Integer, default=0)
    locations_count: Mapped[int] = mapped_column(Integer, default=1)
    social_urls: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    locations: Mapped[list["LocationModel"]] = relationship(back_populates="clinic")
    signals: Mapped[list["SignalModel"]] = relationship(back_populates="clinic")
    score: Mapped["ScoreModel | None"] = relationship(back_populates="clinic")
    enrichment: Mapped["EnrichmentModel | None"] = relationship(back_populates="clinic")


class LocationModel(Base):
    __tablename__ = "location"
    __table_args__ = (Index("ix_location_state_city", "state", "city"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinic.id", ondelete="CASCADE"), nullable=False
    )
    street: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    postal_code: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    lng: Mapped[float | None] = mapped_column(Numeric(9, 6))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    clinic: Mapped["ClinicModel"] = relationship(back_populates="locations")


Index("ix_location_clinic", LocationModel.clinic_id)


class SignalModel(Base):
    __tablename__ = "signal"
    __table_args__ = (Index("uq_signal_clinic_type", "clinic_id", "type", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinic.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    applied_weight: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=1.0)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    clinic: Mapped["ClinicModel"] = relationship(back_populates="signals")


Index("ix_signal_clinic", SignalModel.clinic_id)


class ScoringConfigModel(Base):
    __tablename__ = "scoring_config"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    weights: Mapped[dict] = mapped_column(JSONB, nullable=False)
    bands: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ScoreModel(Base):
    __tablename__ = "score"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinic.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority: Mapped[str] = mapped_column(Text, nullable=False)
    config_version: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("scoring_config.version")
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    clinic: Mapped["ClinicModel"] = relationship(back_populates="score")


Index("ix_score_total", ScoreModel.total.desc())
Index("ix_score_priority", ScoreModel.priority)


class EnrichmentModel(Base):
    __tablename__ = "enrichment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinic.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    growth_probability: Mapped[int | None] = mapped_column(Integer)
    technology_maturity: Mapped[int | None] = mapped_column(Integer)
    marketing_sophistication: Mapped[int | None] = mapped_column(Integer)
    expansion_probability: Mapped[int | None] = mapped_column(Integer)
    explanation: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    input_fingerprint: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    clinic: Mapped["ClinicModel"] = relationship(back_populates="enrichment")


class AppUserModel(Base):
    __tablename__ = "app_user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
