# BACKEND/core/lifecycle.py
from __future__ import annotations
import time
from ..repositories.session_store import STORE


def gc_loop(interval_sec: int = 60):
    while True:
        time.sleep(interval_sec)
        now = time.time()
        for meta in STORE.all():
            expired = (meta.status != "open") or (meta.expires_at < now)
            if expired:
                STORE.delete(meta.session_id)
