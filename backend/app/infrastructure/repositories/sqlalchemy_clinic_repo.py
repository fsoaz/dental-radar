from uuid import UUID

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.domain.entities.clinic import Clinic
from app.domain.entities.location import Location
from app.domain.repositories.clinic_repo import (
    ClinicDetail,
    ClinicListItem,
    ClinicListQuery,
    ClinicListResult,
    ClinicRepository,
)
from app.infrastructure.db.mappers import (
    apply_clinic_entity,
    apply_location_entity,
    clinic_model_to_entity,
    location_model_to_entity,
)
from app.infrastructure.db.models import ClinicModel, LocationModel, ScoreModel, SignalModel


class SqlAlchemyClinicRepository(ClinicRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, clinic: Clinic, primary_location: Location) -> tuple[Clinic, bool]:
        existing = self._session.execute(
            select(ClinicModel).where(ClinicModel.place_id == clinic.place_id)
        ).scalar_one_or_none()

        if existing is not None:
            apply_clinic_entity(existing, clinic)
            existing.updated_at = func.now()

            location_model = self._session.execute(
                select(LocationModel).where(
                    LocationModel.clinic_id == existing.id,
                    LocationModel.is_primary.is_(True),
                )
            ).scalar_one_or_none()

            if location_model is None:
                location_model = LocationModel(
                    id=primary_location.id,
                    clinic_id=existing.id,
                    is_primary=True,
                )
                self._session.add(location_model)

            apply_location_entity(location_model, primary_location)
            self._session.commit()
            self._session.refresh(existing)
            return clinic_model_to_entity(existing), False

        clinic_model = ClinicModel(
            id=clinic.id,
            place_id=clinic.place_id,
            name=clinic.name,
            phone=clinic.phone,
            website=clinic.website,
            google_rating=clinic.google_rating,
            google_review_count=clinic.google_review_count,
            social_urls=list(clinic.social_urls),
        )
        self._session.add(clinic_model)

        location_model = LocationModel(
            id=primary_location.id,
            clinic_id=clinic.id,
            is_primary=True,
        )
        apply_location_entity(location_model, primary_location)
        self._session.add(location_model)

        self._session.commit()
        self._session.refresh(clinic_model)
        return clinic_model_to_entity(clinic_model), True

    def get_detail(self, clinic_id: UUID) -> ClinicDetail | None:
        clinic_model = self._session.execute(
            select(ClinicModel)
            .options(
                selectinload(ClinicModel.locations),
                selectinload(ClinicModel.signals),
                selectinload(ClinicModel.score),
                selectinload(ClinicModel.enrichment),
            )
            .where(ClinicModel.id == clinic_id)
        ).scalar_one_or_none()

        if clinic_model is None:
            return None

        primary = next((loc for loc in clinic_model.locations if loc.is_primary), None)
        if primary is None and clinic_model.locations:
            primary = clinic_model.locations[0]

        score = None
        if clinic_model.score is not None:
            score = {
                "total": clinic_model.score.total,
                "priority": clinic_model.score.priority,
                "breakdown": clinic_model.score.breakdown,
                "config_version": clinic_model.score.config_version,
            }

        enrichment = None
        if clinic_model.enrichment is not None:
            enrichment = {
                "growth_probability": clinic_model.enrichment.growth_probability,
                "technology_maturity": clinic_model.enrichment.technology_maturity,
                "marketing_sophistication": clinic_model.enrichment.marketing_sophistication,
                "expansion_probability": clinic_model.enrichment.expansion_probability,
                "explanation": clinic_model.enrichment.explanation,
            }

        signals = [
            {
                "type": signal.type,
                "applied_weight": signal.applied_weight,
                "evidence": signal.evidence,
                "confidence": float(signal.confidence),
            }
            for signal in clinic_model.signals
        ]

        return ClinicDetail(
            clinic=clinic_model_to_entity(clinic_model),
            primary_location=location_model_to_entity(primary) if primary else None,
            signals=signals,
            score=score,
            enrichment=enrichment,
        )

    def list_clinics(self, query: ClinicListQuery) -> ClinicListResult:
        stmt = select(ClinicModel).options(
            selectinload(ClinicModel.locations),
            selectinload(ClinicModel.score),
            selectinload(ClinicModel.enrichment),
        )

        joined_location = False

        if query.q or query.state:
            stmt = stmt.join(
                LocationModel,
                (LocationModel.clinic_id == ClinicModel.id) & LocationModel.is_primary.is_(True),
            )
            joined_location = True

        if query.q:
            pattern = f"%{query.q}%"
            if not joined_location:
                stmt = stmt.join(
                    LocationModel,
                    (LocationModel.clinic_id == ClinicModel.id)
                    & LocationModel.is_primary.is_(True),
                )
                joined_location = True
            stmt = stmt.where(
                or_(
                    ClinicModel.name.ilike(pattern),
                    LocationModel.city.ilike(pattern),
                )
            )

        if query.state:
            if not joined_location:
                stmt = stmt.join(
                    LocationModel,
                    (LocationModel.clinic_id == ClinicModel.id)
                    & LocationModel.is_primary.is_(True),
                )
                joined_location = True
            stmt = stmt.where(LocationModel.state.ilike(query.state))

        score_total = (
            select(ScoreModel.total)
            .where(ScoreModel.clinic_id == ClinicModel.id)
            .correlate(ClinicModel)
            .scalar_subquery()
        )
        score_priority = (
            select(ScoreModel.priority)
            .where(ScoreModel.clinic_id == ClinicModel.id)
            .correlate(ClinicModel)
            .scalar_subquery()
        )

        if query.priority:
            stmt = stmt.where(score_priority.ilike(query.priority))

        if query.min_score is not None:
            stmt = stmt.where(score_total >= query.min_score)

        if query.max_score is not None:
            stmt = stmt.where(score_total <= query.max_score)

        if query.has_website is True:
            stmt = stmt.where(ClinicModel.website.is_not(None), ClinicModel.website != "")
        elif query.has_website is False:
            stmt = stmt.where(or_(ClinicModel.website.is_(None), ClinicModel.website == ""))

        if query.signal_type:
            stmt = stmt.where(
                exists().where(
                    SignalModel.clinic_id == ClinicModel.id,
                    SignalModel.type.ilike(query.signal_type),
                )
            )

        count_query = select(func.count()).select_from(stmt.subquery())
        total = self._session.execute(count_query).scalar_one()

        if query.sort == "-score":
            order = score_total.desc().nullslast()
        elif query.sort == "score":
            order = score_total.asc().nullsfirst()
        elif query.sort == "name":
            order = ClinicModel.name.asc()
        else:
            order = score_total.desc().nullslast()

        offset = (query.page - 1) * query.page_size
        clinic_models = (
            self._session.execute(stmt.order_by(order).offset(offset).limit(query.page_size))
            .scalars()
            .all()
        )

        items: list[ClinicListItem] = []
        for clinic_model in clinic_models:
            primary = next((loc for loc in clinic_model.locations if loc.is_primary), None)
            if primary is None and clinic_model.locations:
                primary = clinic_model.locations[0]

            items.append(
                ClinicListItem(
                    clinic=clinic_model_to_entity(clinic_model),
                    city=primary.city if primary else None,
                    state=primary.state if primary else None,
                    score=clinic_model.score.total if clinic_model.score else None,
                    priority=clinic_model.score.priority if clinic_model.score else None,
                    growth_probability=(
                        clinic_model.enrichment.growth_probability
                        if clinic_model.enrichment
                        else None
                    ),
                )
            )

        return ClinicListResult(items=items, total=total)

    def update_locations_count(self, clinic_id: UUID, locations_count: int) -> None:
        clinic_model = self._session.get(ClinicModel, clinic_id)
        if clinic_model is None:
            return
        clinic_model.locations_count = locations_count
        clinic_model.updated_at = func.now()
        self._session.commit()

    def list_ids_with_website(self) -> list[UUID]:
        rows = self._session.execute(
            select(ClinicModel.id).where(
                ClinicModel.website.is_not(None),
                ClinicModel.website != "",
            )
        ).scalars()
        return list(rows)

    def list_all_ids(self) -> list[UUID]:
        rows = self._session.execute(select(ClinicModel.id)).scalars()
        return list(rows)
