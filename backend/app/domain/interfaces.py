from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from app.domain.entities import StreamSession, ROIEvent


class IStreamSessionRepository(ABC):
    @abstractmethod
    async def create(self, session: StreamSession) -> StreamSession: ...

    @abstractmethod
    async def get_by_id(self, session_id: uuid.UUID) -> Optional[StreamSession]: ...

    @abstractmethod
    async def update(self, session: StreamSession) -> StreamSession: ...


class IROIEventRepository(ABC):
    @abstractmethod
    async def create(self, event: ROIEvent) -> ROIEvent: ...

    @abstractmethod
    async def get_by_stream_id(
        self,
        stream_id: uuid.UUID,
        from_frame: Optional[int] = None,
        limit: int = 100,
    ) -> List[ROIEvent]: ...
