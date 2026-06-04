from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import require_pipeline_runner
from app.core.database import get_db_session
from app.models.app_user import AppUser
from app.schemas.news import PipelineRunResponse
from app.tasks.pipeline_task import run_pipeline_task

router: APIRouter = APIRouter()
_logger: logging.Logger = logging.getLogger(__name__)


@router.post("/run", response_model=PipelineRunResponse)
def run_pipeline(
    db_session: Session = Depends(get_db_session),
    actor: AppUser = Depends(require_pipeline_runner),
) -> PipelineRunResponse:
    _logger.info(
        "manual_pipeline_requested user_id=%s user_email=%s",
        actor.id,
        actor.email,
    )
    return run_pipeline_task(db_session, swallow_errors=False)
