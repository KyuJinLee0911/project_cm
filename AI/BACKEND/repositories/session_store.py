# BACKEND/repositories/session_store.py
from __future__ import annotations
import threading, time
from dataclasses import dataclass
from typing import List

import numpy as np
from ..core.config import settings

now = lambda: time.time()


@dataclass
class SessionMeta:
    session_id: str
    width: int
    height: int
    created_at: float
    expires_at: float
    image_np: "np.ndarray"
    status: str = "open"  # open|closed

    def touch(self):
        self.expires_at = now() + settings.SESS_TTL_SEC


class SessionStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._by_id: dict[str, SessionMeta] = {}

    def create(self, meta: SessionMeta):
        with self._lock:
            self._by_id[meta.session_id] = meta

    def get_open(self, sid: str) -> SessionMeta:
        with self._lock:
            meta = self._by_id.get(sid)
        if not meta:
            raise KeyError("not_found")
        if meta.status != "open":
            raise RuntimeError("closed")
        if meta.expires_at < now():
            raise TimeoutError("expired")
        return meta

    def close(self, sid: str):
        with self._lock:
            meta = self._by_id.get(sid)
        if not meta:
            raise KeyError("not_found")
        meta.status = "closed"

    def all(self) -> List[SessionMeta]:
        with self._lock:
            return list(self._by_id.values())

    def delete(self, sid: str):
        with self._lock:
            self._by_id.pop(sid, None)


STORE = SessionStore()
