from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.application.use_cases.compute_score import (
    GetRescoreJob,
    GetScoringConfig,
    UpdateScoringConfig,
)
from app.domain.entities.rescore_job import RescoreJob
from app.presentation.api.deps import (
    get_get_rescore_job,
    get_get_scoring_config,
    get_update_scoring_config,
    require_api_key,
)
from app.presentation.api.v1.schemas.scoring_config import (
    RescoreJobResponse,
    ScoreBandResponseSchema,
    ScoringConfigResponse,
    UpdateScoringConfigRequest,
    UpdateScoringConfigResponse,
)

router = APIRouter(prefix="/scoring-config", tags=["scoring-config"])


def _job_response(job: RescoreJob | None) -> RescoreJobResponse | None:
    if job is None:
        return None
    return RescoreJobResponse(
        id=job.id,
        config_version=job.config_version,
        status=job.status,
        rescored=job.rescored,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        message=job.error_message,
    )


@router.get("", response_model=ScoringConfigResponse)
def get_scoring_config(
    use_case: GetScoringConfig = Depends(get_get_scoring_config),
) -> ScoringConfigResponse:
    config, job = use_case.execute()
    return ScoringConfigResponse(
        version=config.version,
        active=config.active,
        weights=config.weights,
        bands=[
            ScoreBandResponseSchema(name=band.name, min=band.min, max=band.max)
            for band in config.bands
        ],
        rescore_job=_job_response(job),
    )


@router.put("", response_model=UpdateScoringConfigResponse, dependencies=[Depends(require_api_key)])
def update_scoring_config(
    body: UpdateScoringConfigRequest,
    response: Response,
    use_case: UpdateScoringConfig = Depends(get_update_scoring_config),
) -> UpdateScoringConfigResponse:
    from app.application.use_cases.compute_score import UpdateScoringConfigRequest as UpdateRequest

    result = use_case.execute(
        UpdateRequest(
            weights=body.weights,
            bands=[band.model_dump() for band in body.bands],
            rescore=body.rescore,
        )
    )
    if result.rescore_job is not None:
        response.status_code = status.HTTP_202_ACCEPTED
    return UpdateScoringConfigResponse(
        version=result.config.version,
        active=result.config.active,
        weights=result.config.weights,
        bands=[
            ScoreBandResponseSchema(name=band.name, min=band.min, max=band.max)
            for band in result.config.bands
        ],
        rescore_job=_job_response(result.rescore_job),
    )


@router.get("/rescore-jobs/{job_id}", response_model=RescoreJobResponse)
def get_rescore_job(
    job_id: UUID,
    use_case: GetRescoreJob = Depends(get_get_rescore_job),
) -> RescoreJobResponse:
    return _job_response(use_case.execute(job_id))  # type: ignore[return-value]
