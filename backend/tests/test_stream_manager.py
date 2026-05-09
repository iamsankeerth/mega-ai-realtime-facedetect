"""
Tests for StreamManager.

Run with:
    pytest tests/test_stream_manager.py -v
"""

import asyncio
import pytest
from app.services.stream_manager import StreamManager, StreamState


@pytest.fixture
def manager():
    """Fresh StreamManager for every test."""
    return StreamManager()


class TestLifecycle:
    """Stream registration, ending, and removal."""

    @pytest.mark.asyncio
    async def test_register_creates_active_stream(self, manager):
        """After register(), stream exists and is ACTIVE."""
        ctx = await manager.register("s1", api_key="secret")
        assert ctx is not None
        assert ctx.state == StreamState.ACTIVE
        assert ctx.meta.stream_id == "s1"
        assert ctx.meta.api_key == "secret"

    @pytest.mark.asyncio
    async def test_end_stream_transitions_state(self, manager):
        """end_stream() changes state to ENDED but keeps context."""
        await manager.register("s1", api_key="secret")
        ctx = await manager.end_stream("s1")
        assert ctx is not None
        assert ctx.state == StreamState.ENDED
        # get() still returns the context (not None)
        assert manager.get("s1") is not None
        assert manager.get("s1").state == StreamState.ENDED

    @pytest.mark.asyncio
    async def test_remove_fully_purges_stream(self, manager):
        """remove() deletes everything from memory."""
        await manager.register("s1", api_key="secret")
        await manager.remove("s1")
        assert manager.get("s1") is None

    @pytest.mark.asyncio
    async def test_register_at_capacity_raises(self, manager):
        """Registering beyond max_streams raises RuntimeError."""
        limited = StreamManager(max_streams=1)
        await limited.register("s1", api_key="secret")
        with pytest.raises(RuntimeError, match="Max streams"):
            await limited.register("s2", api_key="secret")


class TestFrameStorage:
    """push_frame() and get_latest() behavior."""

    @pytest.mark.asyncio
    async def test_push_and_get_roundtrip(self, manager):
        """Push a frame, then get_latest returns it."""
        await manager.register("s1", api_key="secret")
        await manager.push_frame("s1", b"hello", roi={"x": 1})
        frame, roi = await manager.get_latest("s1")
        assert frame == b"hello"
        assert roi == {"x": 1}

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_for_unknown_stream(self, manager):
        """get_latest on never-registered stream returns (None, None)."""
        frame, roi = await manager.get_latest("ghost")
        assert frame is None
        assert roi is None

    @pytest.mark.asyncio
    async def test_push_frame_noop_for_ended_stream(self, manager):
        """push_frame on ENDED stream does nothing."""
        await manager.register("s1", api_key="secret")
        await manager.push_frame("s1", b"first")
        await manager.end_stream("s1")
        # push to ended stream is a no-op
        await manager.push_frame("s1", b"second")
        frame, _ = await manager.get_latest("s1")
        # still returns the last frame pushed while ACTIVE
        assert frame == b"first"

    @pytest.mark.asyncio
    async def test_get_latest_works_for_ended_stream(self, manager):
        """get_latest returns last frame even after stream ended."""
        await manager.register("s1", api_key="secret")
        await manager.push_frame("s1", b"last")
        await manager.end_stream("s1")
        frame, _ = await manager.get_latest("s1")
        assert frame == b"last"


class TestRateLimiting:
    """Frame rate enforcement."""

    @pytest.mark.asyncio
    async def test_check_rate_allows_first_frame(self, manager):
        """First frame always passes rate check."""
        await manager.register("s1", api_key="secret")
        assert await manager.check_rate("s1") is True

    @pytest.mark.asyncio
    async def test_check_rate_rejects_too_soon(self, manager):
        """Second frame too soon is rejected."""
        slow = StreamManager(max_fps=1)  # 1 frame per second = 1s interval
        await slow.register("s1", api_key="secret")
        # Simulate a frame just arriving (push_frame updates last_frame_at)
        await slow.push_frame("s1", b"frame1")
        # Immediately check again — should be too soon
        assert await slow.check_rate("s1") is False

    @pytest.mark.asyncio
    async def test_check_rate_allows_after_interval(self, manager):
        """Frame after min_interval is allowed."""
        fast = StreamManager(max_fps=10)  # 100ms interval
        await fast.register("s1", api_key="secret")
        await fast.push_frame("s1", b"frame1")
        assert await fast.check_rate("s1") is False
        await asyncio.sleep(0.15)  # 150ms > 100ms interval
        assert await fast.check_rate("s1") is True


class TestStats:
    """Statistics tracking."""

    @pytest.mark.asyncio
    async def test_increment_frame_count(self, manager):
        """Stats update after frame increments."""
        await manager.register("s1", api_key="secret")
        manager.increment_frame_count("s1", raw_bytes=1000, annotated_bytes=1200)
        ctx = manager.get("s1")
        assert ctx.stats.frame_count == 1
        assert ctx.stats.bytes_received == 1000
        assert ctx.stats.bytes_annotated == 1200

    @pytest.mark.asyncio
    async def test_increment_detected(self, manager):
        """Detected counter increments."""
        await manager.register("s1", api_key="secret")
        manager.increment_detected("s1")
        assert manager.get("s1").stats.detected_count == 1


class TestSummary:
    """Diagnostics snapshot."""

    @pytest.mark.asyncio
    async def test_summary_reflects_active_streams(self, manager):
        """summary() returns correct counts."""
        await manager.register("s1", api_key="secret")
        await manager.register("s2", api_key="secret")
        await manager.end_stream("s2")
        summary = manager.summary()
        assert summary["total_streams"] == 2
        assert summary["active_streams"] == 1
        assert summary["active_ids"] == ["s1"]
