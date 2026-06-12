import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from utils.env import settings
from utils.logger import get_logger
from utils.custom_errors import APIError
from routes.default import app as default_router
from routes.agent import app as agent_router
from routes.bash import app as bash_router
from contextlib import asynccontextmanager
from langgraph.checkpoint.memory import MemorySaver
from agent.agent import build_graph
from utils.msc import clone_repo

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — building graph and cloning repo")
    app.state.graph = build_graph(MemorySaver())
    clone_repo(settings.REPO_URL, settings.PAT_TOKEN)
    logger.info("Startup complete")
    yield
    logger.info("Shutting down")


app = FastAPI(title="Coding Agent API", lifespan=lifespan)

app.include_router(default_router)
app.include_router(agent_router)
app.include_router(bash_router)


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    logger.error("APIError on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=exc.status_code or 500,
        content={"error": str(exc)},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
