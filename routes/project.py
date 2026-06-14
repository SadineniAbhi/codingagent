from fastapi import APIRouter, Depends
from utils.logger import get_logger
from utils.env import settings
from utils.auth import validate_token
from payloads.project import CreateProjectRequest
from service.project_service import s_create_project, s_list_projects

app = APIRouter(prefix=settings.PATH_PREFIX)
logger = get_logger(__name__)


@app.get("/projects")
async def list_projects(claims=Depends(validate_token)):
    logger.info("GET /projects")
    return await s_list_projects(user_id=claims["sub"])


@app.post("/project")
async def create_project(body: CreateProjectRequest, claims=Depends(validate_token)):
    logger.info("POST /project")
    return await s_create_project(body, user_id=claims["sub"])
