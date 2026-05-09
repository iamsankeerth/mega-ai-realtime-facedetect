import uuid
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.domain.interfaces import IROIEventRepository
from app.infrastructure.db import async_session
from app.repositories.postgres_roi import PostgresROIEventRepository

router = APIRouter()


class ROIEventResponse(BaseModel):
    id: str
    stream_id: str
    frame_no: int
    ts_ms: int
    x: float
    y: float
    w: float
    h: float
    confidence: float
    dropped_frame_count: int

    class Config:
        from_attributes = True


class ROIListResponse(BaseModel):
    stream_id: str
    count: int
    events: List[ROIEventResponse]


@router.get("/{stream_id}/rois", response_model=ROIListResponse)
async def get_rois(
    stream_id: str,
    from_frame: Optional[int] = Query(None, ge=0, description="Filter events from this frame number"),
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
):
    try:
        stream_uuid = uuid.UUID(stream_id)
    except ValueError:
        # Match the ingest endpoint logic: deterministic UUID from string
        stream_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, stream_id)

    async with async_session() as db_session:
        repo = PostgresROIEventRepository(db_session)
        events = await repo.get_by_stream_id(
            stream_id=stream_uuid,
            from_frame=from_frame,
            limit=limit,
        )

    return ROIListResponse(
        stream_id=stream_id,
        count=len(events),
        events=[
            ROIEventResponse(
                id=str(e.id),
                stream_id=str(e.stream_id),
                frame_no=e.frame_no,
                ts_ms=e.ts_ms,
                x=e.x,
                y=e.y,
                w=e.w,
                h=e.h,
                confidence=e.confidence,
                dropped_frame_count=e.dropped_frame_count,
            )
            for e in events
        ],
    )
