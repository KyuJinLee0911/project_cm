from core.redis_pubsub import publisher

result = publisher.publish_status(job_id="job123", status="downloading", progress=10, message="downloading...")
print(f"Status published: {result}")

result = publisher.publish_result(
  job_id="job123", 
  result={
    "frames": 100, 
    "drop": {"frame" : 50, "confidence": 0.95},
    "average_score": 95
    }
  )
print(f"Result published: {result}")

result = publisher.publish_error(job_id="job123", error_message="An error occurred")
print(f"Error published: {result}")