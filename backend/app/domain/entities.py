from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class StreamSession:
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: str = "active"
    source_meta: Optional[str] = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class ROIEvent:
    stream_id: uuid.UUID
    frame_no: int
    ts_ms: int
    x: float
    y: float
    w: float
    h: float
    confidence: float
    dropped_frame_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
