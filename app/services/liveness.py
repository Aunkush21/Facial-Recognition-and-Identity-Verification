from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from app.core.config import settings

MODEL_PATH = Path(__file__).resolve().parent.parent / "models_data" / "liveness" / "minifasnet_v2.onnx"
INPUT_SIZE = 80
CROP_SCALE = 2.7  # matches the "2.7_80x80" MiniFASNet-V2 training crop


def _expand_and_crop(bgr_image: np.ndarray, bbox: tuple[int, int, int, int], scale: float = CROP_SCALE) -> np.ndarray:
    """Crop a `scale`x margin around the face box, keeping the face centred.

    Matches Silent-Face-Anti-Spoofing's crop: the scale is capped so the box
    fits the image, and when the expanded box runs past an edge it is *shifted*
    back in (preserving size) rather than clamped — clamping off-centres faces
    near the frame border and degrades the liveness prediction.
    """
    x1, y1, x2, y2 = bbox
    src_h, src_w = bgr_image.shape[:2]
    box_w, box_h = x2 - x1, y2 - y1

    scale = min((src_h - 1) / box_h, (src_w - 1) / box_w, scale)
    new_w, new_h = box_w * scale, box_h * scale
    cx, cy = x1 + box_w / 2, y1 + box_h / 2

    left, top = cx - new_w / 2, cy - new_h / 2
    right, bottom = cx + new_w / 2, cy + new_h / 2
    if left < 0:
        right -= left
        left = 0
    if top < 0:
        bottom -= top
        top = 0
    if right > src_w - 1:
        left -= right - src_w + 1
        right = src_w - 1
    if bottom > src_h - 1:
        top -= bottom - src_h + 1
        bottom = src_h - 1

    crop = bgr_image[int(top):int(bottom) + 1, int(left):int(right) + 1]
    return cv2.resize(crop, (INPUT_SIZE, INPUT_SIZE))


class LivenessChecker:
    """Wraps a MiniFASNet-V2 ONNX model (Silent-Face-Anti-Spoofing).

    The model emits a 3-class softmax. In this model **index 1 is the live/real
    class** (matching the upstream reference: `if argmax == 1: RealFace`), while
    indices 0 and 2 are spoof classes. Index 0 in particular is near-zero for
    every input — an earlier version read it as the "live" score, which rejected
    every face (real or not) as a spoof.
    """

    REAL_CLASS_INDEX = 1

    def __init__(self, model_path: Path | None = None):
        self._session = ort.InferenceSession(str(model_path or MODEL_PATH), providers=["CPUExecutionProvider"])
        self._input_name = self._session.get_inputs()[0].name

    def is_live(self, bgr_image: np.ndarray, bbox: tuple[int, int, int, int]) -> tuple[bool, float]:
        crop = _expand_and_crop(bgr_image, bbox)
        # This ONNX export bakes the /255 normalization INTO the graph, so it
        # expects raw 0-255 float pixels. Dividing by 255 here double-normalizes
        # and collapses the output to a meaningless constant class — verified
        # empirically (raw input gives confident, discriminating predictions;
        # /255 input flattens every face, live or spoof, to ~0.99 on one class).
        blob = crop.astype(np.float32)
        blob = np.transpose(blob, (2, 0, 1))[np.newaxis, ...]  # NCHW

        raw = self._session.run(None, {self._input_name: blob})[0][0]
        # The exported graph may or may not include a trailing softmax node;
        # only normalize ourselves if the raw output isn't already a distribution.
        if np.isclose(raw.sum(), 1.0, atol=1e-3) and raw.min() >= 0:
            probs = raw
        else:
            shifted = np.exp(raw - raw.max())
            probs = shifted / shifted.sum()

        liveness_score = float(probs[self.REAL_CLASS_INDEX])
        return liveness_score >= settings.liveness_threshold, liveness_score


_checker: LivenessChecker | None = None


def get_liveness_checker() -> LivenessChecker:
    global _checker
    if _checker is None:
        _checker = LivenessChecker()
    return _checker
