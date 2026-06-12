from utils.env import settings
from utils.logger import get_logger
from fastapi import APIRouter, Request, Depends
from payloads.agent import Execute, ResumeRequest

from utils.auth import validate_token
from service.agent_service import s_run, s_resume, s_get_state

app = APIRouter(prefix=settings.PATH_PREFIX)
logger = get_logger(__name__)

@app.post("/agent/run")
async def run(task: Execute, request: Request, cliams = Depends(validate_token)):
    logger.info("POST /agent/run")
    graph = request.app.state.graph
    return await s_run("default", task, graph)


@app.post("/agent/resume")
async def resume(body: ResumeRequest, request: Request, cliams = Depends(validate_token)):
    logger.info("POST /agent/resume")
    graph = request.app.state.graph
    return await s_resume("default", body.input, graph)


@app.get("/agent/state")
async def get_state(request: Request, cliams = Depends(validate_token)):
    logger.info("GET /agent/state")
    graph = request.app.state.graph
    return await s_get_state("default", graph)
