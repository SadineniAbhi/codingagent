from fastapi import APIRouter
from utils.env import settings
from utils.logger import get_logger

app = APIRouter(prefix=settings.PATH_PREFIX)
logger = get_logger(__name__)

@app.get("/health")
async def health():
    logger.info("GET /health")
    return {"status": "ok"}
