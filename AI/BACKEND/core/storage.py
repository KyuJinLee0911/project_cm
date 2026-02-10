# BACKEND/core/storage.py
from __future__ import annotations
import os, shutil, uuid
from PIL import Image
from .config import settings


os.makedirs(settings.STORAGE_DIR, exist_ok=True)


def save_upload_image(upload_file) -> tuple[str, int, int]:
    ext = os.path.splitext(upload_file.filename or "")[1].lower() or ".png"
    path = os.path.join(settings.STORAGE_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    im = Image.open(path).convert("RGB")
    w, h = im.size
    return path, w, h


def remove_file(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
