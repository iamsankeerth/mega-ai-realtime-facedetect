from dataclasses import dataclass
from typing import Optional
import numpy as np
import mediapipe as mp


@dataclass
class DetectionResult:
    x: float
    y: float
    w: float
    h: float
    confidence: float


class FaceDetector:
    """MediaPipe face detection using Task API (v0.10.35+)."""

    def __init__(self, min_detection_confidence: float = 0.5):
        base_options = mp.tasks.BaseOptions(
            model_asset_path="face_detection_short_range.tflite"
        )
        options = mp.tasks.vision.FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=min_detection_confidence,
        )
        self._detector = mp.tasks.vision.FaceDetector.create_from_options(options)

    def detect(self, image: np.ndarray) -> Optional[DetectionResult]:
        """Detect face in RGB numpy array. Returns first detection or None."""
        h, w = image.shape[:2]
        
        # Convert numpy array to MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        
        results = self._detector.detect(mp_image)
        if not results.detections:
            return None

        # Take first face
        detection = results.detections[0]
        bbox = detection.bounding_box
        
        return DetectionResult(
            x=float(bbox.origin_x),
            y=float(bbox.origin_y),
            w=float(bbox.width),
            h=float(bbox.height),
            confidence=float(detection.categories[0].score),
        )

    def close(self):
        self._detector.close()
