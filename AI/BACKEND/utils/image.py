# BACKEND/utils/image.py
from __future__ import annotations
import numpy as np
from PIL import Image

try:
    import cv2
except Exception:
    cv2 = None


class CVUnavailable(RuntimeError): ...


def ensure_cv2():
    if cv2 is None:
        raise CVUnavailable("OpenCV(cv2) 설치 필요: pip install opencv-python")


def read_image_to_numpy(fp: str) -> np.ndarray:
    im = Image.open(fp).convert("RGB")
    return np.array(im)
