# BACKEND/core/redis_pubsub.py
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class RedisPublisher:
    """
    Redis Pub/Sub Publisher for analysis results.
    Publishes analysis completion events to Redis channel.

    Backend(Spring Boot)와 동일한 채널 및 메시지 형식 사용:
    - 채널: ai_job_result
    - 메시지: {job_id, status, message, result}
    """

    _instance: Optional["RedisPublisher"] = None
    _client: Optional[redis.Redis] = None
    
    STREAM_NAME = "ai_job_result_stream"
    USE_STREAM = True
    
    def __init__(self):
        self._client = None
        self._connect()
        
    def _connect(self):
        try:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Connection test
            self._client.ping()
            logger.info(
                f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}"
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}. Pub/Sub disabled.")
            self._client = None

    def __new__(cls) -> "RedisPublisher":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_client(self) -> redis.Redis:
        """Lazy initialization of Redis client."""
        if self._client is None:
            self._connect()
        return self._client

    def _publish(self, payload: dict[str, Any]) -> bool:
        """
        Publish message to Redis (Pub/Sub or Stream)
        
        Args:
            payload: Message payload (must contain job_id, status, message, result)
        
        Returns:
            True if published successfully, False otherwise
        """
        client = self._get_client()
        if client is None:
            return False
        
        if self.USE_STREAM:
            return self._publish_to_stream(payload)
        
        return self._publish_to_pubsub(payload)

    def _publish_to_stream(self, payload: dict[str, Any]) -> bool:
        """
        새로운 Stream 방식
        
        메시지 구조 : 
        {
            "job_id": str,
            "eventType": "status" | "result" | "error",
            "timestamp": "2024-06-01T12:00:00",
            "data": "{...}" # JSON 문자열   
        }
        """
        client = self._get_client()
        try:
            job_id = payload.get("job_id")
            status = payload.get("status")
            
            if status in ["succeeded", "completed"]:
                event_type = "result"
            elif status in ["failed", "error"]:
                event_type = "error"
            else:
                event_type = "status"

            # Prepare stream message
            stream_message = {
                "job_id": job_id,
                "eventType": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": json.dumps(payload, ensure_ascii=False)
            }
            
            message_id = client.xadd(self.STREAM_NAME, stream_message, maxlen=10000)

            # Publish to stream
            logger.info(f"Published to stream {message_id}: job_id={job_id}, status={status}, eventType={event_type}")
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to publish to stream: {e}")
            return False

    def _publish_to_pubsub(self, payload: dict[str, Any]) -> bool:
        """
        Publish message to Redis channel.

        Args:
            payload: Message payload (must contain job_id, status, message, result)

        Returns:
            True if published successfully, False otherwise
        """
        client = self._get_client()
        try:
            subscribers = client.publish(
                settings.REDIS_CHANNEL,
                json.dumps(payload, ensure_ascii=False)
            )
            logger.info(
                f"Published to {settings.REDIS_CHANNEL}: "
                f"job_id={payload.get('job_id')}, status={payload.get('status')} "
                f"({subscribers} subscribers)"
            )
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to publish: {e}")
            return False

    def publish_status(
        self,
        job_id: str,
        status: str,
        progress: int = 0,
        message: Optional[str] = None,
    ) -> bool:
        """
        Publish job status update to Redis channel.
        Backend에서 진행 상황을 확인할 수 있도록 상태 업데이트 전송.

        Args:
            job_id: The job identifier
            status: Current status (queued, downloading, skeletonizing, analyzing, succeeded, failed)
            progress: Progress percentage (0-100)
            message: Optional status message

        Returns:
            True if published successfully, False otherwise
        """
        payload = {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "message": message or status,
            "result": None,
        }
        return self._publish(payload)

    def publish_result(
        self,
        job_id: str,
        result: dict[str, Any],
    ) -> bool:
        """
        Publish analysis result to Redis channel.
        분석 완료 시 최종 결과를 Backend로 전송.

        Args:
            job_id: The job identifier
            result: The analysis result dictionary

        Returns:
            True if published successfully, False otherwise
        """
        payload = {
            "job_id": job_id,
            "status": "succeeded",
            "message": "analysis complete",
            "result": result,
        }
        return self._publish(payload)

    def publish_error(
        self,
        job_id: str,
        error_message: str,
    ) -> bool:
        """
        Publish error event to Redis channel.
        분석 실패 시 에러 메시지를 Backend로 전송.

        Args:
            job_id: The job identifier
            error_message: The error message

        Returns:
            True if published successfully, False otherwise
        """
        payload = {
            "job_id": job_id,
            "status": "failed",
            "message": error_message,
            "result": None,
        }
        return self._publish(payload)

    def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            try:
                self._client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._client = None


# Singleton instance
publisher = RedisPublisher()
