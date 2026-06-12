from fastapi import APIRouter
from payloads.agent import BashRequest
from service.bash_service import run_command

app = APIRouter()

@app.post("/bash")
async def bash(body: BashRequest):
    result = run_command(body.command)
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
