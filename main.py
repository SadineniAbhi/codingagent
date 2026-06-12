import uvicorn
from fastapi import FastAPI

from env import settings
from routes.default import app as default_router
from routes.agent import app as agent_router
from routes.bash import app as bash_router
from contextlib import asynccontextmanager
from utils.lifespan_utils import clone_repo
from agent.agent import build_graph





@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = build_graph()
    clone_repo(settings.REPO_URL, settings.PAT_TOKEN)
    yield


app = FastAPI(title="Coding Agent API", lifespan=lifespan)
app.include_router(default_router)
app.include_router(agent_router)
app.include_router(bash_router)



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
