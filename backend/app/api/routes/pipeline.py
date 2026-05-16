from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.auth_staff import require_staff_pipeline_runner
from app.core.database import get_db_session
from app.models.staff_user import StaffUser
from app.schemas.news import PipelineRunResponse
from app.tasks.pipeline_task import run_pipeline_task

router: APIRouter = APIRouter()
_logger: logging.Logger = logging.getLogger(__name__)


@router.post("/run", response_model=PipelineRunResponse)
def run_pipeline(
    db_session: Session = Depends(get_db_session),
    staff_user: StaffUser = Depends(require_staff_pipeline_runner),
) -> PipelineRunResponse:
    _logger.info(
        "manual_pipeline_requested staff_user_id=%s staff_email=%s",
        staff_user.id,
        staff_user.email,
    )
    return run_pipeline_task(db_session, swallow_errors=False)
