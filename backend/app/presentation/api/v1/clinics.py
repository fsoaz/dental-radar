from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.application.use_cases.compute_score import ComputeScore
from app.application.use_cases.detect_signals import DetectSignals, ListClinicSignals
from app.application.use_cases.discover_clinics import DiscoverClinics
from app.application.use_cases.enrich_clinic import EnrichClinic
from app.application.use_cases.list_clinics import GetClinic, ListClinics
from app.domain.entities.signal import Signal
from app.domain.repositories.clinic_repo import ClinicListQuery
from app.presentation.api.deps import (
    get_compute_score,
    get_detect_signals,
    get_discover_clinics,
    get_enrich_clinic,
    get_get_clinic,
    get_list_clinic_signals,
    get_list_clinics,
)
from app.presentation.api.v1.schemas.clinic import (
    AddressResponse,
    ClinicDetailResponse,
    ClinicListItemResponse,
    ClinicListResponse,
    ComputeScoreResponse,
    DetectSignalsResponse,
    DiscoverClinicsRequest,
    DiscoverClinicsResponse,
    EnrichClinicResponse,
    EnrichmentResponse,
    ErrorResponse,
    ScoreResponse,
    SignalListResponse,
    SignalResponse,
)


def _signal_to_response(signal: Signal) -> SignalResponse:
    return SignalResponse(
        type=signal.type.value,
        applied_weight=signal.applied_weight,
        evidence=signal.evidence,
        confidence=signal.confidence,
        detected_at=signal.detected_at,
    )


router = APIRouter(prefix="/clinics", tags=["clinics"])


@router.post(
    "/discover",
    response_model=DiscoverClinicsResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def discover_clinics(
    body: DiscoverClinicsRequest,
    use_case: DiscoverClinics = Depends(get_discover_clinics),
) -> DiscoverClinicsResponse:
    result = use_case.execute(body.query)
    return DiscoverClinicsResponse(
        ingested=result.ingested,
        created=result.created,
        updated=result.updated,
    )


@router.get("", response_model=ClinicListResponse)
def list_clinics(
    q: str | None = Query(default=None),
    state: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    min_score: int | None = Query(default=None, ge=0),
    max_score: int | None = Query(default=None, ge=0),
    has_website: bool | None = Query(default=None),
    signal_type: str | None = Query(default=None),
    sort: str = Query(default="-score"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    use_case: ListClinics = Depends(get_list_clinics),
) -> ClinicListResponse:
    result = use_case.execute(
        ClinicListQuery(
            q=q,
            state=state,
            priority=priority,
            min_score=min_score,
            max_score=max_score,
            has_website=has_website,
            signal_type=signal_type,
            sort=sort,
            page=page,
            page_size=page_size,
        )
    )
    return ClinicListResponse(
        data=[
            ClinicListItemResponse(
                id=item.clinic.id,
                name=item.clinic.name,
                city=item.city,
                state=item.state,
                score=item.score,
                priority=item.priority,
                growth_probability=item.growth_probability,
            )
            for item in result.items
        ],
        page=page,
        page_size=page_size,
        total=result.total,
    )


@router.post(
    "/{clinic_id}/signals:detect",
    response_model=DetectSignalsResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={404: {"model": ErrorResponse}},
)
def detect_clinic_signals(
    clinic_id: UUID,
    use_case: DetectSignals = Depends(get_detect_signals),
) -> DetectSignalsResponse:
    result = use_case.execute(clinic_id)
    return DetectSignalsResponse(
        detected=result.detected,
        signals=[_signal_to_response(signal) for signal in result.signals],
        skipped=result.skipped,
        skip_reason=result.skip_reason,
    )


@router.get(
    "/{clinic_id}/signals",
    response_model=SignalListResponse,
    responses={404: {"model": ErrorResponse}},
)
def list_clinic_signals(
    clinic_id: UUID,
    use_case: ListClinicSignals = Depends(get_list_clinic_signals),
) -> SignalListResponse:
    signals = use_case.execute(clinic_id)
    return SignalListResponse(data=[_signal_to_response(signal) for signal in signals])


@router.post(
    "/{clinic_id}/score",
    response_model=ComputeScoreResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={404: {"model": ErrorResponse}},
)
def compute_clinic_score(
    clinic_id: UUID,
    use_case: ComputeScore = Depends(get_compute_score),
) -> ComputeScoreResponse:
    result = use_case.execute(clinic_id)
    return ComputeScoreResponse(
        clinic_id=result.clinic_id,
        total=result.total,
        priority=result.priority,
        breakdown=result.breakdown,
        config_version=result.config_version,
    )


@router.post(
    "/{clinic_id}/enrich",
    response_model=EnrichClinicResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def enrich_clinic(
    clinic_id: UUID,
    force: bool = Query(default=False),
    use_case: EnrichClinic = Depends(get_enrich_clinic),
) -> EnrichClinicResponse:
    result = use_case.execute(clinic_id, force=force)
    return EnrichClinicResponse(
        clinic_id=result.clinic_id,
        growth_probability=result.growth_probability,
        technology_maturity=result.technology_maturity,
        marketing_sophistication=result.marketing_sophistication,
        expansion_probability=result.expansion_probability,
        explanation=result.explanation,
        provider=result.provider,
        model=result.model,
        prompt_version=result.prompt_version,
        skipped=result.skipped,
        skip_reason=result.skip_reason,
    )


@router.get(
    "/{clinic_id}",
    response_model=ClinicDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_clinic(
    clinic_id: UUID,
    use_case: GetClinic = Depends(get_get_clinic),
) -> ClinicDetailResponse:
    detail = use_case.execute(clinic_id)

    address = None
    if detail.primary_location is not None:
        addr = detail.primary_location.address
        address = AddressResponse(
            street=addr.street,
            city=addr.city,
            state=addr.state,
            postal_code=addr.postal_code,
            country=addr.country,
        )

    score = None
    if detail.score is not None:
        score = ScoreResponse(**detail.score)

    enrichment = None
    if detail.enrichment is not None:
        enrichment = EnrichmentResponse(**detail.enrichment)

    return ClinicDetailResponse(
        id=detail.clinic.id,
        name=detail.clinic.name,
        place_id=detail.clinic.place_id,
        address=address,
        phone=detail.clinic.phone,
        website=detail.clinic.website,
        google_rating=detail.clinic.google_rating,
        google_review_count=detail.clinic.google_review_count,
        locations_count=detail.clinic.locations_count,
        services=detail.clinic.services,
        social_urls=detail.clinic.social_urls,
        signals=[SignalResponse(**signal) for signal in detail.signals],
        score=score,
        enrichment=enrichment,
    )
