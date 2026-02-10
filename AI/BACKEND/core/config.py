# BACKEND/core/config.py
from __future__ import annotations
import os


class Settings:
    APP_NAME: str = "Climbmate AI API"
    VERSION: str = "1.0.0"
    SESS_TTL_SEC: int = int(os.getenv("SESS_TTL_SEC", "1800"))  # 30분
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage")
    CORS_ALLOW_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    ]

    # Redis 설정
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Redis Pub/Sub 채널 (Backend와 동일하게 설정)
    REDIS_CHANNEL: str = os.getenv("REDIS_CHANNEL", "ai_job_result")
    
    # Redis Stream 사용 여부
    REDIS_USE_STREAM: bool = os.getenv("REDIS_USE_STREAM", "true")
    REDIS_STREAM_NAME: str = os.getenv("REDIS_STREAM_NAME", "ai_job_result_stream")

settings = Settings()
