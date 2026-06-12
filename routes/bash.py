from fastapi import APIRouter
from payloads.agent import BashRequest
from service.bash_service import run_command
from utils.logger import get_logger

app = APIRouter()
logger = get_logger(__name__)

@app.post("/bash")
async def bash(body: BashRequest):
    logger.info("POST /bash")
    result = run_command(body.command)
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
