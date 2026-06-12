from fastapi import APIRouter
from env import settings

app = APIRouter(prefix=settings.PATH_PREFIX)

@app.get("/health")
async def health():
    return {"status": "ok"}
