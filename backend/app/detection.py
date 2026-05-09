"""
Face detection module without OpenCV.
Uses MediaPipe for detection and Pillow for image manipulation.
"""

from PIL import Image, ImageDraw
import numpy as np
import mediapipe as mp
from typing import Optional, Tuple, List

mp_face_detection = mp.solutions.face_detection
face_detector = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

def detect_face(pil_image: Image.Image) -> Optional[Tuple[int, int, int, int]]:
    """
    Detect a single face in a PIL Image.
    Returns (x, y, width, height) for the axis-aligned minimal bounding box,
    or None if no face is detected.
    """
    # Convert PIL Image to RGB numpy array
    image_np = np.array(pil_image.convert("RGB"))
    
    results = face_detector.process(image_np)
    if not results.detections:
        return None
    
    # Assume only one face (per assignment constraints)
    detection = results.detections[0]
    bbox = detection.location_data.relative_bounding_box
    
    img_width, img_height = pil_image.size
    
    x = int(bbox.xmin * img_width)
    y = int(bbox.ymin * img_height)
    width = int(bbox.width * img_width)
    height = int(bbox.height * img_height)
    
    return (x, y, width, height)

def draw_roi(pil_image: Image.Image, bbox: Tuple[int, int, int, int]) -> Image.Image:
    """
    Draw an axis-aligned bounding box on the image.
    Returns a new PIL Image with the rectangle drawn.
    """
    image_copy = pil_image.copy()
    draw = ImageDraw.Draw(image_copy)
    x, y, w, h = bbox
    draw.rectangle([x, y, x + w, y + h], outline="red", width=3)
    return image_copy
