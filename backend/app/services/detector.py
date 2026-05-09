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
    """MediaPipe face detection wrapper. No OpenCV imports."""

    def __init__(self, min_detection_confidence: float = 0.5):
        self._detector = mp.solutions.face_detection.FaceDetection(
            min_detection_confidence=min_detection_confidence,
            model_selection=0,  # short-range model, good for webcam/close faces
        )

    def detect(self, image: np.ndarray) -> Optional[DetectionResult]:
        """
        Detect face in RGB numpy array.
        Returns first detection as DetectionResult or None.
        """
        # MediaPipe expects RGB uint8
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)

        results = self._detector.process(image)
        if not results.detections:
            return None

        detection = results.detections[0]  # single-face assumption
        bbox = detection.location_data.relative_bounding_box
        h, w = image.shape[:2]

        x = max(0.0, bbox.xmin) * w
        y = max(0.0, bbox.ymin) * h
        box_w = bbox.width * w
        box_h = bbox.height * h
        confidence = detection.score[0]

        return DetectionResult(
            x=x,
            y=y,
            w=box_w,
            h=box_h,
            confidence=confidence,
        )

    def close(self):
        self._detector.close()
