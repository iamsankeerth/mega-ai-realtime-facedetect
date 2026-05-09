import asyncio

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.services.stream_manager import stream_manager

router = APIRouter()

# MJPEG boundary string
BOUNDARY = "frame-boundary"


async def mjpeg_generator(stream_id: str, fps: int = 10):
    """Yield multipart JPEG frames from the stream manager."""
    interval = 1.0 / fps
    while True:
        # Check if stream was fully removed (not just ended)
        ctx = stream_manager.get(stream_id)
        if ctx is None:
            break

        frame, _ = await stream_manager.get_latest(stream_id)
        if frame is None:
            # Stream not active — wait and retry
            await asyncio.sleep(interval)
            continue

        yield (
            b"--" + BOUNDARY.encode() + b"\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: " + str(len(frame)).encode() + b"\r\n"
            b"\r\n" + frame + b"\r\n"
        )
        await asyncio.sleep(interval)


@router.get("/{stream_id}/video")
async def serve_video(stream_id: str, fps: int = Query(10, ge=1, le=30)):
    if stream_manager.get(stream_id) is None:
        raise HTTPException(status_code=404, detail="STREAM_NOT_FOUND")

    return StreamingResponse(
        mjpeg_generator(stream_id, fps=fps),
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
