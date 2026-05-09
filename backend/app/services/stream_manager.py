"""
Stream Manager — centralized stream lifecycle and rate limiting.

Replaces informal global singletons (frame_buffer, ingest-level tracking) with a
single injectable service that owns:
  • Stream registry (active / paused / ended)
  • Latest annotated frame buffer
  • Stream metadata and statistics
  • Rate-limit enforcement
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class StreamState(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


@dataclass
class StreamStats:
    """Mutable statistics updated every frame."""

    frame_count: int = 0
    detected_count: int = 0
    dropped_count: int = 0
    last_frame_at: float = field(default_factory=time.time)
    bytes_received: int = 0
    bytes_annotated: int = 0


@dataclass
class StreamMeta:
    """Immutable metadata created at stream start."""

    stream_id: str
    api_key: str
    started_at: float = field(default_factory=time.time)
    source_meta: Optional[str] = None


@dataclass
class StreamContext:
    """Everything the backend knows about one stream."""

    meta: StreamMeta
    state: StreamState = StreamState.ACTIVE
    stats: StreamStats = field(default_factory=StreamStats)
    latest_frame: Optional[bytes] = None
    latest_roi: Optional[dict] = None


class StreamManager:
    """
    Thread-safe manager for all active streams.

    Usage (inside FastAPI dependency or WebSocket handler):
        manager = StreamManager()
        ctx = manager.register("demo-stream", api_key="secret")
        manager.push_frame("demo-stream", jpeg_bytes, roi={...})
        frame, roi = manager.get_latest("demo-stream")
        manager.end_stream("demo-stream")
    """

    # ─── Configurable limits ───
    DEFAULT_MAX_STREAMS: int = 100
    DEFAULT_MAX_FPS: float = 20.0          # ingest rate limit

    def __init__(
        self,
        *,
        max_streams: int = DEFAULT_MAX_STREAMS,
        max_fps: float = DEFAULT_MAX_FPS,
    ):
        self._max_streams = max_streams
        self._max_fps = max_fps
        self._min_interval = 1.0 / max_fps

        # Core storage
        self._streams: Dict[str, StreamContext] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

        # House-keeping
        self._global_lock = asyncio.Lock()

    # ─── Lifecycle ───

    async def register(self, stream_id: str, api_key: str, source_meta: Optional[str] = None) -> StreamContext:
        """Create a new stream context. Raises RuntimeError if at capacity."""
        async with self._global_lock:
            if len(self._streams) >= self._max_streams:
                raise RuntimeError(f"Max streams ({self._max_streams}) reached")

            meta = StreamMeta(stream_id=stream_id, api_key=api_key, source_meta=source_meta)
            ctx = StreamContext(meta=meta)
            self._streams[stream_id] = ctx
            self._locks[stream_id] = asyncio.Lock()
            return ctx

    async def end_stream(self, stream_id: str) -> Optional[StreamContext]:
        """Mark stream ended. Keeps stats and latest frame for reporting."""
        async with self._global_lock:
            ctx = self._streams.get(stream_id)
            if ctx is None:
                return None
            ctx.state = StreamState.ENDED
            return ctx

    async def remove(self, stream_id: str) -> None:
        """Fully purge stream from memory (use after end_stream + grace period)."""
        async with self._global_lock:
            self._streams.pop(stream_id, None)
            self._locks.pop(stream_id, None)

    # ─── Read ───

    def get(self, stream_id: str) -> Optional[StreamContext]:
        return self._streams.get(stream_id)

    def is_active(self, stream_id: str) -> bool:
        ctx = self._streams.get(stream_id)
        return ctx is not None and ctx.state == StreamState.ACTIVE

    def list_active(self) -> List[str]:
        return [
            sid for sid, ctx in self._streams.items()
            if ctx.state == StreamState.ACTIVE
        ]

    # ─── Latest annotated frame (MJPEG serve) ───

    async def push_frame(self, stream_id: str, frame_bytes: bytes, roi: Optional[dict] = None) -> None:
        """Update latest annotated frame + ROI for video endpoint. No-op if stream not active."""
        lock = self._locks.get(stream_id)
        if lock is None:
            return
        async with lock:
            ctx = self._streams.get(stream_id)
            if ctx is None or ctx.state != StreamState.ACTIVE:
                return
            ctx.latest_frame = frame_bytes
            ctx.latest_roi = roi
            ctx.stats.last_frame_at = time.time()

    async def get_latest(self, stream_id: str) -> tuple[Optional[bytes], Optional[dict]]:
        """Return (frame_bytes, roi_dict) for MJPEG streaming.

        Works for both ACTIVE and ENDED streams so the video endpoint can serve
        the last frame after the WebSocket disconnects (graceful shutdown).
        """
        lock = self._locks.get(stream_id)
        if lock is None:
            return None, None
        async with lock:
            ctx = self._streams.get(stream_id)
            if ctx is None:
                return None, None
            return ctx.latest_frame, ctx.latest_roi

    # ─── Rate limiting ───

    async def check_rate(self, stream_id: str) -> bool:
        """Return True if stream is allowed to send another frame NOW."""
        ctx = self._streams.get(stream_id)
        if ctx is None:
            return False
        now = time.time()
        elapsed = now - ctx.stats.last_frame_at
        return elapsed >= self._min_interval

    # ─── Stats helpers ───

    def increment_detected(self, stream_id: str) -> None:
        ctx = self._streams.get(stream_id)
        if ctx:
            ctx.stats.detected_count += 1

    def increment_dropped(self, stream_id: str) -> None:
        ctx = self._streams.get(stream_id)
        if ctx:
            ctx.stats.dropped_count += 1

    def increment_frame_count(self, stream_id: str, raw_bytes: int, annotated_bytes: int) -> None:
        ctx = self._streams.get(stream_id)
        if ctx:
            ctx.stats.frame_count += 1
            ctx.stats.bytes_received += raw_bytes
            ctx.stats.bytes_annotated += annotated_bytes

    # ─── Diagnostics ───

    def summary(self) -> dict:
        """Quick health snapshot for /health or logging."""
        active = self.list_active()
        return {
            "total_streams": len(self._streams),
            "active_streams": len(active),
            "active_ids": active,
            "max_streams": self._max_streams,
            "max_fps": self._max_fps,
        }


# ─── Global singleton (replace with dependency injection in production) ───
stream_manager = StreamManager()
