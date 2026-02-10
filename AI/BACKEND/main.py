# BACKEND/main.py
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.hold_routes import router as hold_router
from .api.analysis_routes import router as analysis_router
from .core.lifecycle import gc_loop
from .core.redis_pubsub import publisher
import threading

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # GC 루프 시작
    threading.Thread(target=gc_loop, daemon=True).start()


@app.on_event("shutdown")
def on_shutdown():
    # Redis 연결 종료
    publisher.close()


app.include_router(hold_router, prefix="/ai/v1")
app.include_router(analysis_router, prefix="/ai/v1")
