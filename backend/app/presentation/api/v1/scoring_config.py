from fastapi import APIRouter, Depends

from app.application.use_cases.compute_score import GetScoringConfig, UpdateScoringConfig
from app.presentation.api.deps import (
    get_get_scoring_config,
    get_update_scoring_config,
    require_api_key,
)
from app.presentation.api.v1.schemas.scoring_config import (
    ScoreBandResponseSchema,
    ScoringConfigResponse,
    UpdateScoringConfigRequest,
    UpdateScoringConfigResponse,
)

router = APIRouter(prefix="/scoring-config", tags=["scoring-config"])


@router.get("", response_model=ScoringConfigResponse)
def get_scoring_config(
    use_case: GetScoringConfig = Depends(get_get_scoring_config),
) -> ScoringConfigResponse:
    config = use_case.execute()
    return ScoringConfigResponse(
        version=config.version,
        active=config.active,
        weights=config.weights,
        bands=[
            ScoreBandResponseSchema(name=band.name, min=band.min, max=band.max)
            for band in config.bands
        ],
    )


@router.put("", response_model=UpdateScoringConfigResponse, dependencies=[Depends(require_api_key)])
def update_scoring_config(
    body: UpdateScoringConfigRequest,
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
    return UpdateScoringConfigResponse(
        version=result.config.version,
        active=result.config.active,
        weights=result.config.weights,
        bands=[
            ScoreBandResponseSchema(name=band.name, min=band.min, max=band.max)
            for band in result.config.bands
        ],
        rescored=result.rescored,
    )
