from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.news import PipelineRunResponse
from app.tasks.pipeline_task import run_pipeline_task

router: APIRouter = APIRouter()


@router.post("/run", response_model=PipelineRunResponse)
def run_pipeline(db_session: Session = Depends(get_db_session)) -> PipelineRunResponse:
    return run_pipeline_task(db_session, swallow_errors=False)
