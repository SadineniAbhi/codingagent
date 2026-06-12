from env import settings
from fastapi import APIRouter, Request
from payloads.agent import Execute, ResumeRequest

from service.agent_service import s_run, s_resume, s_get_state

app = APIRouter(prefix=settings.PATH_PREFIX)

@app.post("/agent/run")
async def run(task: Execute, request: Request):
    graph = request.app.state.graph
    return await s_run("default", task, graph)


@app.post("/agent/resume")
async def resume(body: ResumeRequest, request: Request):
    graph = request.app.state.graph
    return await s_resume("default", body.input, graph)


@app.get("/agent/state")
async def get_state(request: Request):
    graph = request.app.state.graph
    return await s_get_state("default", graph)
