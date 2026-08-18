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
from app.infrastructure.db.models import (
    ClinicModel,
    LocationModel,
    ScoreModel,
    SignalModel,
)


def _escape_like(term: str) -> str:
    """Escape LIKE metacharacters so user input is matched literally."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


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
                "detected_at": signal.detected_at,
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
        def filtered_ids(*, scored: bool | None = None):
            if scored is True:
                stmt = select(ClinicModel.id).select_from(ScoreModel).join(ClinicModel)
            else:
                stmt = select(ClinicModel.id).select_from(ClinicModel)
                if query.priority or query.min_score is not None or query.max_score is not None:
                    stmt = stmt.join(ScoreModel, ScoreModel.clinic_id == ClinicModel.id)
                if scored is False:
                    stmt = stmt.where(~exists().where(ScoreModel.clinic_id == ClinicModel.id))

            if query.q or query.state:
                stmt = stmt.join(
                    LocationModel,
                    (LocationModel.clinic_id == ClinicModel.id)
                    & LocationModel.is_primary.is_(True),
                )
            if query.q:
                pattern = f"%{_escape_like(query.q)}%"
                stmt = stmt.where(
                    or_(
                        ClinicModel.name.ilike(pattern, escape="\\"),
                        LocationModel.city.ilike(pattern, escape="\\"),
                    )
                )
            if query.state:
                stmt = stmt.where(LocationModel.state.ilike(_escape_like(query.state), escape="\\"))
            if query.priority:
                stmt = stmt.where(ScoreModel.priority == query.priority.upper())
            if query.min_score is not None:
                stmt = stmt.where(ScoreModel.total >= query.min_score)
            if query.max_score is not None:
                stmt = stmt.where(ScoreModel.total <= query.max_score)
            if query.has_website is True:
                stmt = stmt.where(ClinicModel.website.is_not(None), ClinicModel.website != "")
            elif query.has_website is False:
                stmt = stmt.where(or_(ClinicModel.website.is_(None), ClinicModel.website == ""))
            if query.signal_type:
                stmt = stmt.where(
                    exists().where(
                        SignalModel.clinic_id == ClinicModel.id,
                        SignalModel.type == query.signal_type.upper(),
                    )
                )
            return stmt

        all_ids = filtered_ids()
        total = self._session.execute(
            select(func.count()).select_from(all_ids.subquery())
        ).scalar_one()
        offset = (query.page - 1) * query.page_size
        selected_ids: list[UUID] = []

        if query.sort == "name":
            selected_ids = list(
                self._session.execute(
                    all_ids.order_by(ClinicModel.name.asc(), ClinicModel.id.asc())
                    .offset(offset)
                    .limit(query.page_size)
                ).scalars()
            )
        else:
            has_score_filters = bool(
                query.priority or query.min_score is not None or query.max_score is not None
            )
            unscored_count = 0
            if not has_score_filters:
                unscored_count = self._session.execute(
                    select(func.count()).select_from(filtered_ids(scored=False).subquery())
                ).scalar_one()
            scored_count = total - unscored_count

            def append_ids(stmt, partition_offset: int, count: int) -> None:
                if count <= 0:
                    return
                selected_ids.extend(
                    self._session.execute(stmt.offset(partition_offset).limit(count)).scalars()
                )

            if query.sort == "score":
                # NULLS FIRST: unscored clinics precede scored clinics.
                unscored_take = max(0, min(query.page_size, unscored_count - offset))
                append_ids(
                    filtered_ids(scored=False).order_by(
                        ClinicModel.name.asc(), ClinicModel.id.asc()
                    ),
                    min(offset, unscored_count),
                    unscored_take,
                )
                remaining = query.page_size - len(selected_ids)
                append_ids(
                    filtered_ids(scored=True).order_by(
                        ScoreModel.total.asc(), ClinicModel.id.asc()
                    ),
                    max(0, offset - unscored_count),
                    remaining,
                )
            else:
                # NULLS LAST: drive the ranked partition from ix_score_total.
                scored_take = max(0, min(query.page_size, scored_count - offset))
                append_ids(
                    filtered_ids(scored=True).order_by(
                        ScoreModel.total.desc(), ClinicModel.id.asc()
                    ),
                    min(offset, scored_count),
                    scored_take,
                )
                remaining = query.page_size - len(selected_ids)
                append_ids(
                    filtered_ids(scored=False).order_by(
                        ClinicModel.name.asc(), ClinicModel.id.asc()
                    ),
                    max(0, offset - scored_count),
                    remaining,
                )

        if selected_ids:
            loaded = (
                self._session.execute(
                    select(ClinicModel)
                    .where(ClinicModel.id.in_(selected_ids))
                    .options(
                        selectinload(ClinicModel.locations),
                        selectinload(ClinicModel.score),
                        selectinload(ClinicModel.enrichment),
                    )
                )
                .scalars()
                .all()
            )
            by_id = {model.id: model for model in loaded}
            clinic_models = [by_id[clinic_id] for clinic_id in selected_ids]
        else:
            clinic_models = []

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
