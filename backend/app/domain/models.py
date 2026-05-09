from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.infrastructure.db import Base


class StreamSession(Base):
    __tablename__ = "stream_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    source_meta = Column(String(255), nullable=True)

    rois = relationship("ROIEvent", back_populates="stream", cascade="all, delete-orphan")


class ROIEvent(Base):
    __tablename__ = "roi_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stream_id = Column(UUID(as_uuid=True), ForeignKey("stream_sessions.id", ondelete="CASCADE"), nullable=False)
    frame_no = Column(Integer, nullable=False)
    ts_ms = Column(Integer, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    w = Column(Float, nullable=False)
    h = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    dropped_frame_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    stream = relationship("StreamSession", back_populates="rois")

    __table_args__ = (
        Index("ix_roi_events_stream_frame", "stream_id", "frame_no"),
        Index("ix_roi_events_stream_ts", "stream_id", "ts_ms"),
    )
