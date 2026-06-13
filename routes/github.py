from utils.env import settings
from utils.logger import get_logger
from fastapi import APIRouter, Depends
from utils.auth import validate_token
from payloads.github import VerifyTokenRequest
from service.github import s_verify_token, s_list_repos

app = APIRouter(prefix=settings.PATH_PREFIX)
logger = get_logger(__name__)


@app.post("/github/verify-token")
async def verify_token(body: VerifyTokenRequest, _=Depends(validate_token)):
    logger.info("POST /github/verify-token")
    await s_verify_token(body.token)
    return {"status": "ok"}


@app.post("/github/list-repos")
async def list_repos(body: VerifyTokenRequest, _=Depends(validate_token)):
    logger.info("POST /github/list-repos")
    return await s_list_repos(body.token)
