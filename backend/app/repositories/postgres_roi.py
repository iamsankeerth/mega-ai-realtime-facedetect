from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import StreamSession, ROIEvent
from app.domain.interfaces import IStreamSessionRepository, IROIEventRepository
from app.domain.models import StreamSession as StreamSessionORM, ROIEvent as ROIEventORM


class PostgresStreamSessionRepository(IStreamSessionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, session: StreamSession) -> StreamSession:
        orm = StreamSessionORM(
            id=session.id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            status=session.status,
            source_meta=session.source_meta,
        )
        self._session.add(orm)
        await self._session.commit()
        return session

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[StreamSession]:
        result = await self._session.execute(
            select(StreamSessionORM).where(StreamSessionORM.id == session_id)
        )
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return StreamSession(
            id=orm.id,
            started_at=orm.started_at,
            ended_at=orm.ended_at,
            status=orm.status,
            source_meta=orm.source_meta,
        )

    async def update(self, session: StreamSession) -> StreamSession:
        result = await self._session.execute(
            select(StreamSessionORM).where(StreamSessionORM.id == session.id)
        )
        orm = result.scalar_one()
        orm.status = session.status
        orm.ended_at = session.ended_at
        orm.source_meta = session.source_meta
        await self._session.commit()
        return session


class PostgresROIEventRepository(IROIEventRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: ROIEvent) -> ROIEvent:
        orm = ROIEventORM(
            id=event.id,
            stream_id=event.stream_id,
            frame_no=event.frame_no,
            ts_ms=event.ts_ms,
            x=event.x,
            y=event.y,
            w=event.w,
            h=event.h,
            confidence=event.confidence,
            dropped_frame_count=event.dropped_frame_count,
            created_at=event.created_at,
        )
        self._session.add(orm)
        await self._session.commit()
        return event

    async def get_by_stream_id(
        self,
        stream_id: uuid.UUID,
        from_frame: Optional[int] = None,
        limit: int = 100,
    ) -> List[ROIEvent]:
        query = select(ROIEventORM).where(ROIEventORM.stream_id == stream_id)
        if from_frame is not None:
            query = query.where(ROIEventORM.frame_no >= from_frame)
        query = query.order_by(ROIEventORM.frame_no).limit(limit)
        result = await self._session.execute(query)
        orms = result.scalars().all()
        return [
            ROIEvent(
                id=orm.id,
                stream_id=orm.stream_id,
                frame_no=orm.frame_no,
                ts_ms=orm.ts_ms,
                x=orm.x,
                y=orm.y,
                w=orm.w,
                h=orm.h,
                confidence=orm.confidence,
                dropped_frame_count=orm.dropped_frame_count,
                created_at=orm.created_at,
            )
            for orm in orms
        ]
