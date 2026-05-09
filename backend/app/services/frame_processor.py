import io
from dataclasses import dataclass
from typing import Optional
import numpy as np
from PIL import Image, ImageDraw

from app.services.detector import FaceDetector, DetectionResult


@dataclass
class ProcessedFrame:
    annotated_bytes: bytes
    roi: Optional[DetectionResult]
    dropped: bool = False


class FrameProcessor:
    """
    Decode binary frame → detect face → draw ROI → encode to JPEG.
    No OpenCV used anywhere.
    """

    def __init__(self, detector: FaceDetector):
        self._detector = detector

    def process(self, frame_data: bytes) -> ProcessedFrame:
        try:
            image = self._decode(frame_data)
        except Exception:
            return ProcessedFrame(annotated_bytes=frame_data, roi=None, dropped=True)

        roi = self._detector.detect(image)
        annotated = self._draw_roi(image, roi)
        encoded = self._encode_jpeg(annotated)

        return ProcessedFrame(annotated_bytes=encoded, roi=roi, dropped=False)

    @staticmethod
    def _decode(frame_data: bytes) -> np.ndarray:
        """Decode JPEG bytes to RGB numpy array for MediaPipe."""
        img = Image.open(io.BytesIO(frame_data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        return np.array(img)

    @staticmethod
    def _draw_roi(image: np.ndarray, roi: Optional[DetectionResult]) -> np.ndarray:
        """Draw axis-aligned bounding box using Pillow."""
        pil_image = Image.fromarray(image)
        if roi is not None:
            draw = ImageDraw.Draw(pil_image)
            draw.rectangle(
                [int(roi.x), int(roi.y), int(roi.x + roi.w), int(roi.y + roi.h)],
                outline=(46, 196, 182),  # #2EC4B6 accent color
                width=3,
            )
        return np.array(pil_image)

    @staticmethod
    def _encode_jpeg(image: np.ndarray) -> bytes:
        """Encode numpy array to JPEG bytes using Pillow."""
        pil_image = Image.fromarray(image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()
