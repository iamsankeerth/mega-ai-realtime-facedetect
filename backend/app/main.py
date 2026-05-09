from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ingest, video, roi
from app.infrastructure.db import engine
from app.domain.models import Base

app = FastAPI(title="Mega AI Face Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/streams")
app.include_router(video.router, prefix="/streams")
app.include_router(roi.router, prefix="/streams")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
