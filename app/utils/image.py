import cv2
import numpy as np


class InvalidImage(Exception):
    pass


def decode_upload_to_bgr(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise InvalidImage("Could not decode uploaded file as an image.")
    return image
