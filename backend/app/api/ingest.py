import asyncio
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.config import settings
from app.domain.entities import StreamSession, ROIEvent
from app.infrastructure.db import async_session
from app.repositories.postgres_roi import PostgresStreamSessionRepository, PostgresROIEventRepository
from app.services.detector import FaceDetector
from app.services.frame_processor import FrameProcessor
from app.services.stream_manager import stream_manager

logger = logging.getLogger(__name__)

router = APIRouter()


detector = FaceDetector(min_detection_confidence=0.5)
processor = FrameProcessor(detector=detector)


@router.websocket("/{stream_id}/ingest")
async def ingest_ws(
    websocket: WebSocket,
    stream_id: str,
    api_key: str = Query(...),
):
    if api_key != settings.api_key:
        await websocket.close(code=1008, reason="Invalid API key")
        return

    await websocket.accept()
    try:
        stream_uuid = uuid.UUID(stream_id)
    except ValueError:
        # Generate a deterministic UUID from the stream_id string
        stream_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, stream_id)

    # Register stream with lifecycle manager
    try:
        await stream_manager.register(stream_id, api_key=api_key)
    except RuntimeError as e:
        logger.warning("Stream registration failed: %s", e)
        await websocket.close(code=1013, reason="Server at capacity")
        return

    # Ensure stream session exists in DB (one-time, short-lived session)
    try:
        async with async_session() as db_session:
            stream_repo = PostgresStreamSessionRepository(db_session)
            session = await stream_repo.get_by_id(stream_uuid)
            if not session:
                session = StreamSession(id=stream_uuid)
                await stream_repo.create(session)
    except Exception as e:
        logger.warning("Failed to create stream session in DB: %s", e)

    frame_count = 0
    dropped_count = 0

    try:
        while True:
            try:
                message = await websocket.receive()
            except WebSocketDisconnect:
                break

            if message.get("type") == "websocket.disconnect":
                break

            if "bytes" not in message:
                continue

            frame_data = message["bytes"]
            frame_count += 1

            try:
                result = processor.process(frame_data)
            except Exception as e:
                logger.warning("Frame processing failed for stream=%s: %s", stream_id, e)
                dropped_count += 1
                continue

            if result.dropped:
                dropped_count += 1

            # Update stream manager with latest annotated frame
            roi_dict = None
            if result.roi:
                roi_dict = {
                    "x": result.roi.x,
                    "y": result.roi.y,
                    "w": result.roi.w,
                    "h": result.roi.h,
                    "confidence": result.roi.confidence,
                }
            await stream_manager.push_frame(stream_id, result.annotated_bytes, roi_dict)

            # Persist ROI if detected (per-frame DB session)
            if result.roi:
                try:
                    async with async_session() as db_session:
                        roi_repo = PostgresROIEventRepository(db_session)
                        event = ROIEvent(
                            stream_id=stream_uuid,
                            frame_no=frame_count,
                            ts_ms=int(asyncio.get_event_loop().time() * 1000),
                            x=result.roi.x,
                            y=result.roi.y,
                            w=result.roi.w,
                            h=result.roi.h,
                            confidence=result.roi.confidence,
                            dropped_frame_count=dropped_count,
                        )
                        await roi_repo.create(event)
                        dropped_count = 0
                except Exception as e:
                    # Graceful degradation: don't crash stream on DB error
                    logger.warning("ROI persist failed for stream=%s: %s", stream_id, e)

            # Send acknowledgment with ROI data for real-time frontend updates
            ack = {
                "frame_no": frame_count,
                "detected": result.roi is not None,
                "dropped": result.dropped,
            }
            if result.roi:
                ack["roi"] = {
                    "x": result.roi.x,
                    "y": result.roi.y,
                    "w": result.roi.w,
                    "h": result.roi.h,
                    "confidence": result.roi.confidence,
                }
            await websocket.send_json(ack)

    except WebSocketDisconnect:
        pass
    finally:
        # Update session status to ended (short-lived session)
        try:
            async with async_session() as db_session:
                stream_repo = PostgresStreamSessionRepository(db_session)
                session = await stream_repo.get_by_id(stream_uuid)
                if session:
                    from datetime import datetime
                    session.status = "ended"
                    session.ended_at = datetime.utcnow()
                    await stream_repo.update(session)
        except Exception as e:
            logger.warning("Failed to mark stream ended in DB: %s", e)

        await stream_manager.end_stream(stream_id)
