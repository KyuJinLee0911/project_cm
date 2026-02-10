# ClimbMate AI

클라이밍 영상 분석을 위한 AI 모듈 및 FastAPI 백엔드 서버입니다.

## 프로젝트 구조

```
AI/
├── AI/                         # AI 분석 로직 모듈
│   ├── fall/                   # 낙하 분석 파이프라인
│   ├── grab/                   # 스켈레톤 추출
│   ├── hold_detect/            # 홀드 인식
│   ├── pose_detect/            # 자세 감지 (YOLO11x-pose)
│   ├── score/                  # 자세 점수 계산
│   ├── main.py                 # 전체 파이프라인 실행
│   └── requirements.txt        # 의존성
├── BACKEND/                    # FastAPI 백엔드 서버
│   ├── api/                    # REST API 라우트
│   ├── core/                   # 설정 및 파이프라인
│   ├── logic/                  # 분석 로직
│   ├── models/                 # Pydantic 스키마
│   ├── repositories/           # 데이터 저장소
│   ├── services/               # 서비스 레이어
│   ├── utils/                  # 유틸리티
│   ├── main.py                 # FastAPI 앱 엔트리포인트
│   └── requirement.txt         # 의존성
└── README.md
```

## 기술 스택

| 분류 | 기술 |
|------|------|
| **Framework** | FastAPI |
| **Deep Learning** | PyTorch, Ultralytics (YOLO11x) |
| **Computer Vision** | OpenCV, Pillow |
| **Data Processing** | NumPy, SciPy |
| **Validation** | Pydantic |
| **Real-time** | Redis Stream |

## AI 분석 모듈 (AI/AI)

### 1. 자세 감지 (pose_detect)
- **YOLO11x-pose** 모델을 사용한 실시간 자세 추정
- 17개 키포인트 추출 (COCO 형식)
- Kalman Filter를 이용한 키포인트 스무딩

### 2. 홀드 인식 (hold_detect)
- **YOLOv8 커스텀 모델** (climbingcrux_model.pt)
- 클릭 좌표 기반 홀드 탐지
- 윤곽선 기반 폴리곤 추출

### 3. 스켈레톤 추출 (grab)
- 영상에서 프레임별 스켈레톤 데이터 추출
- 홀드 터치 감지
- 스켈레톤 시계열 데이터 저장 (.npy)

### 4. 자세 점수 계산 (score)
- 무게중심 분석
- 몸통 각도 계산
- 관절 각도 (팔/다리) 분석
- 안정성 점수 산출

### 5. 낙하 분석 (fall)
8단계 파이프라인으로 구성:

| 단계 | 파일 | 설명 |
|------|------|------|
| Step 3 | `step3_processing.py` | 스켈레톤 데이터 전처리, 스무딩 |
| Step 4 | `step4_events.py` | 낙하 이벤트 감지 (t_drop, t_touch) |
| Step 5 | `step5_height.py` | 낙하 높이 및 체공시간 추정 |
| Step 6 | `step6_gate.py` | 낮은 낙하 조기 종료 판단 |
| Step 7 | `step7_rules.py` | 착지 분석 및 분류 |
| Step 8 | `step8_report.py` | 최종 리포트 생성 |

## FastAPI 백엔드 (AI/BACKEND)

### API 엔드포인트

#### 홀드 인식 API (`/ai/v1/hold`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/sessions` | 이미지 업로드 및 세션 생성 |
| POST | `/sessions/{session_id}/holds:detect` | 좌표 기반 홀드 인식 |
| GET | `/sessions/{session_id}` | 세션 정보 조회 |
| POST | `/sessions/{session_id}:close` | 세션 종료 |

#### 분석 API (`/ai/v1/analysis`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/jobs` | 분석 작업 생성 및 시작 |
| GET | `/jobs/{job_id}` | 작업 상태 조회 |
| GET | `/jobs/{job_id}/result` | 분석 결과 조회 |

### 분석 파이프라인

```
1. queued       → 작업 대기열 등록
2. downloading  → 영상 다운로드
3. skeletonizing → 스켈레톤 추출
4. analyzing    → 자세/낙하 분석
5. succeeded    → 완료
```

### Redis Stream (실시간 결과 전송)

분석 진행 상황과 결과를 Redis Stream을 통해 Backend(Spring Boot)로 전송합니다.

> **Note**: v1.2.0부터 Redis Pub/Sub 대신 Redis Stream을 사용합니다.
> Stream은 메시지 영속성, Consumer Group, ACK 메커니즘을 제공하여 메시지 유실을 방지합니다.

#### Stream 이름
```
ai_job_result_stream
```

#### 메시지 형식

Stream에 저장되는 메시지 구조:

```json
{
  "job_id": "abc123",
  "eventType": "status | result | error",
  "timestamp": "2024-01-01T12:00:00",
  "data": "{...}"  // JSON 문자열로 직렬화된 payload
}
```

#### eventType별 data 내용

**1. status (상태 업데이트)**
```json
{
  "job_id": "abc123",
  "status": "analyzing",
  "progress": 50,
  "message": "analyzing fall...",
  "result": null
}
```

**2. result (분석 완료)**
```json
{
  "job_id": "abc123",
  "status": "succeeded",
  "message": "analysis complete",
  "result": {
    "frames": [...],
    "drop": {...},
    "average_score": 82.5
  }
}
```

**3. error (에러 발생)**
```json
{
  "job_id": "abc123",
  "status": "failed",
  "message": "download error: connection timeout",
  "result": null
}
```

#### Python 코드 (메시지 발행)

```python
# redis_pubsub.py
class RedisPublisher:
    STREAM_NAME = "ai_job_result_stream"

    def _publish_to_stream(self, payload: dict) -> bool:
        stream_message = {
            "job_id": payload.get("job_id"),
            "eventType": self._get_event_type(payload.get("status")),
            "timestamp": datetime.now().isoformat(),
            "data": json.dumps(payload)
        }
        message_id = self._client.xadd(self.STREAM_NAME, stream_message)
        return True
```

#### Backend 연동 (Spring Boot)

Backend의 `RedisStreamConfig`에서 `@Scheduled` polling으로 메시지를 수신하고,
`AiJobStreamListener`에서 메시지를 처리합니다.

```java
// RedisStreamConfig.java
@Scheduled(fixedDelay = 500)
public void pollMessages() {
    List<MapRecord<String, Object, Object>> messages = redisTemplate.opsForStream().read(
        Consumer.from(CONSUMER_GROUP, CONSUMER_NAME),
        StreamReadOptions.empty().count(10).block(Duration.ofMillis(100)),
        StreamOffset.create(STREAM_KEY, ReadOffset.lastConsumed())
    );
    // 메시지 처리 후 ACK
}
```

#### Redis Stream vs Pub/Sub 비교

| 항목 | Pub/Sub (이전) | Stream (현재) |
|------|----------------|---------------|
| 메시지 영속성 | 없음 | 있음 |
| Consumer 오프라인 | 메시지 유실 | 나중에 수신 가능 |
| 재처리 | 불가능 | Pending에서 재처리 |
| ACK | 없음 | 지원 |
| 모니터링 | 어려움 | XINFO, XPENDING |

### 분석 결과 스키마

```json
{
  "job_id": "uuid",
  "status": "succeeded",
  "frames": [
    {
      "frame_idx": 0,
      "skeleton": [[x, y], ...],
      "tri_quad": [...],
      "body_center": [x, y],
      "tri_quad_center": [x, y],
      "metrics": {
        "tilt_pct": 85.0,
        "flexion_pct": 78.0,
        "com_pct": 90.0,
        "avg_pct": 84.3,
        "stability": "stable"
      }
    }
  ],
  "drop": {
    "t_drop": 150,
    "t_touch": 180,
    "message": "피드백 메시지",
    "landing_sequence": ["feet", "knees", "hands"]
  },
  "average_score": 82.5
}
```

## 실행 방법

### AI 분석 모듈 실행

```bash
cd AI/AI

# 의존성 설치
pip install -r requirements.txt

# 전체 파이프라인 실행
python main.py
```

### FastAPI 서버 실행

```bash
cd AI/BACKEND

# 의존성 설치
pip install -r requirement.txt

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 환경 변수

```bash
# 세션 TTL (초, 기본 1800초 = 30분)
SESS_TTL_SEC=1800

# 저장 디렉토리
STORAGE_DIR=./storage

# CORS 허용 도메인
CORS_ALLOW_ORIGINS=*

# Redis 설정
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=           # 비밀번호 (선택)
REDIS_DB=0
REDIS_STREAM_NAME=ai_job_result_stream
```

## 모델 파일

| 모델 | 용도 | 경로 |
|------|------|------|
| `yolo11x-pose.pt` | 자세 추정 | `AI/model/` |
| `climbingcrux_model.pt` | 홀드 인식 | `AI/model/` |

## 분석 지표

### 자세 분석 지표
- **tilt_pct**: 몸통 기울기 점수 (0-100%)
- **flexion_pct**: 관절 굴곡 점수
- **com_pct**: 무게중심 안정성 점수 (0-100%)
- **avg_pct**: 전체 평균 점수 (0-100%)
- **stability**: 안정성 상태 (stable/unstable)

### 낙하 분석 지표
- **t_drop**: 낙하 시작 프레임
- **t_touch**: 착지 프레임
- **landing_sequence**: 착지 순서 (예: feet → knees → hands)
- **landing_type**: 착지 유형 분류

## 변경 이력

### v1.2.0 - Redis Stream 전환
- **Redis Pub/Sub → Redis Stream 전환**
  - 메시지 영속성 확보 (Consumer 오프라인 시에도 메시지 유실 없음)
  - Consumer Group 기반 메시지 관리
  - ACK 메커니즘으로 처리 완료 확인
  - Pending 메시지 재처리 지원
- **메시지 구조 변경**
  - `eventType` 필드 추가 (status/result/error)
  - `timestamp` 필드 추가
  - `data` 필드에 JSON 직렬화된 payload 저장
- **Backend 연동 방식 변경**
  - `@Scheduled` polling 방식으로 메시지 수신
  - `XREADGROUP` 명령으로 Consumer Group 기반 읽기

### v1.1.0 - Redis Pub/Sub 지원 (Deprecated)
- **Redis Pub/Sub 추가**: 분석 진행 상황 및 결과를 실시간으로 전송
  - 상태 업데이트 (status): 각 단계별 진행률 전송
  - 분석 결과 (result): 완료 시 전체 결과 전송
  - 에러 (error): 실패 시 에러 메시지 전송
- **폴링 방식과 병행**: 기존 REST API 폴링 방식도 계속 지원
- **Graceful degradation**: Redis 연결 실패 시에도 서비스 정상 동작
- ⚠️ **v1.2.0에서 Redis Stream으로 대체됨**

### v1.0.0 - 초기 버전
- FastAPI 기반 AI 분석 서버
- 홀드 인식 및 자세 분석 기능
- REST API 폴링 방식 결과 조회
