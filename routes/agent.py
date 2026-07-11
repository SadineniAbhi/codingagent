from utils.env import settings
from utils.logger import get_logger
from fastapi import APIRouter, Depends
from payloads.agent import Execute
from utils.auth import validate_token
from service.agent_service import AgentService
from dependencies import get_agent_service

app = APIRouter(prefix=settings.PATH_PREFIX)
logger = get_logger(__name__)


@app.post("/agent/run")
async def run(task: Execute, _=Depends(validate_token), service: AgentService = Depends(get_agent_service)):
    logger.info("POST /agent/run")
    return await service.s_run("default", task)


@app.get("/agent/state")
async def get_state(_=Depends(validate_token), service: AgentService = Depends(get_agent_service)):
    logger.info("GET /agent/state")
    return await service.s_get_state("default")
