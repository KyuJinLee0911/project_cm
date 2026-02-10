# ClimbMate

실내 스포츠 클라이밍 운동 영상을 AI로 분석하는 플랫폼입니다.

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | ClimbMate |
| **설명** | 클라이밍 운동 영상의 AI 기반 자세 분석 및 홀드 인식 플랫폼 |
| **Java 버전** | 17 |
| **Spring Boot** | 3.5.7 |
| **빌드 도구** | Gradle |

## 프로젝트 구조

```
project_cm/
├── Backend/                    # Java Spring Boot 백엔드 서버
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/          # Java 소스 코드
│   │   │   └── resources/     # 설정 파일
│   │   └── test/              # 테스트 코드
│   ├── build.gradle           # Gradle 빌드 설정
│   ├── Dockerfile             # Docker 빌드 설정
│   └── Jenkinsfile            # CI/CD 파이프라인
├── AI/                         # AI 분석 서버
│   ├── AI/                     # AI 분석 로직 모듈
│   │   ├── fall/               # 낙하 분석
│   │   ├── grab/               # 스켈레톤 추출
│   │   ├── hold_detect/        # 홀드 인식
│   │   ├── pose_detect/        # 자세 감지
│   │   └── score/              # 점수 계산
│   └── BACKEND/                # FastAPI 백엔드 서버
│       ├── api/                # REST API 라우트
│       ├── core/               # 설정 및 파이프라인
│       ├── services/           # 서비스 레이어
│       └── models/             # Pydantic 스키마
└── README.md                   # 프로젝트 문서
```

## 기술 스택

### Backend (Java)
| 분류 | 기술 |
|------|------|
| **Framework** | Spring Boot 3.5.7 |
| **Security** | Spring Security + JWT |
| **Database** | PostgreSQL, Redis |
| **ORM** | Spring Data JPA |
| **Cloud Storage** | AWS S3 |
| **Real-time** | WebSocket (STOMP), Redis Stream |
| **API Docs** | SpringDoc OpenAPI (Swagger) |
| **Build** | Gradle |
| **Containerization** | Docker |

### AI Server (Python)
| 분류 | 기술 |
|------|------|
| **Framework** | FastAPI |
| **Deep Learning** | PyTorch, Ultralytics (YOLO11x) |
| **Computer Vision** | OpenCV, Pillow |
| **Data Processing** | NumPy, SciPy |
| **Pose Estimation** | YOLO11x-pose |
| **Validation** | Pydantic |

## 주요 기능

### 1. 사용자 관리
- 이메일 기반 회원가입/로그인
- JWT 토큰 인증 (Access + Refresh Token)
- 사용자 프로필 관리 (키, 몸무게, 팔 길이)

### 2. 영상 관리
- AWS S3 Presigned URL을 통한 안전한 영상 업로드
- 영상 메타데이터 저장 및 조회
- 날짜별 영상 필터링

### 3. 운동 세션 & 시도 관리
- 운동 세션 생성/종료/조회
- 난이도별 운동 시도 기록
- 운동 시간 자동 계산

### 4. AI 홀드 인식
- **YOLOv8 커스텀 모델** 기반 홀드 탐지
- 클릭 좌표 기반 홀드 자동 인식
- 윤곽선 기반 폴리곤 추출
- 홀드 좌표, 타입, 폴리곤 정보 저장

### 5. AI 자세 분석
- **YOLO11x-pose** 모델 기반 자세 추정
- 17개 키포인트 추출 (COCO 형식)
- Kalman Filter 기반 키포인트 스무딩
- 무게중심, 몸통 각도, 관절 각도 분석
- 안정성 점수 (0-100%) 산출

### 6. AI 낙하 분석
- 낙하 이벤트 자동 감지 (t_drop, t_touch)
- 낙하 높이 및 체공시간 추정
- 착지 유형 분류 및 분석
- 착지 순서 추적 (feet → knees → hands)

## 데이터 모델

```
User (사용자)
 └── 1:N → ExerciseSession (운동 세션)
              └── 1:N → Trial (운동 시도)
                         └── 1:N → Video (운동 영상)
                                    ├── 1:1 → ExerciseInfo (운동 정보)
                                    ├── 1:N → Hold (홀드 인식 결과)
                                    └── 1:1 → AnalyzedData (자세 분석 결과)
```

### 엔티티 상세

| 엔티티 | 설명 | 주요 필드 |
|--------|------|-----------|
| **User** | 사용자 정보 | email, password, nickname, height, weight, reach |
| **ExerciseSession** | 운동 세션 | location, startedAt, endedAt, duration |
| **Trial** | 운동 시도 | difficulty |
| **Video** | 운동 영상 | vFileKey, tFileKey, sessionId, isAnalyzed |
| **ExerciseInfo** | 운동 정보 | startedAt, endedAt, isSuccesses |
| **Hold** | 홀드 인식 결과 | x, y, polygon, bbox, holdType |
| **AnalyzedData** | 자세 분석 결과 | status, message, resultJson |

## API 엔드포인트

### 인증 API (`/api/v1/auth`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/login` | 로그인 |
| POST | `/logout` | 로그아웃 |
| POST | `/reissue` | 토큰 재발급 |

### 사용자 API (`/api/v1/users`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/` | 회원가입 |
| GET | `/` | 회원 정보 조회 |
| PUT | `/` | 회원 정보 수정 |
| GET | `/email` | 이메일 중복 확인 |
| DELETE | `/` | 회원 탈퇴 |

### 영상 API (`/api/v1/videos`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/pre-signed` | 업로드 URL 요청 |
| POST | `/` | 영상 정보 등록 |
| GET | `/` | 영상 목록 조회 |
| GET | `/{video_id}` | 영상 상세 조회 |

### 홀드 인식 API (`/api/v1/videos/{video_id}/holds/detect`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/open` | 홀드 인식 세션 시작 |
| POST | `/` | 홀드 인식 요청 |
| DELETE | `/{hold_id}` | 홀드 삭제 |
| DELETE | `/` | 홀드 인식 취소 |

### 자세 분석 API (`/api/v1/videos/{video_id}/analysis`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/` | 자세 분석 요청 |
| GET | `/` | 분석 결과 조회 |

### 운동 세션 API (`/api/v1/sessions`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/` | 세션 생성 |
| GET | `/` | 세션 목록 조회 |
| GET | `/{session_id}` | 세션 상세 조회 |
| PUT | `/{session_id}` | 세션 종료 |
| DELETE | `/{session_id}` | 세션 삭제 |

### 운동 시도 API (`/api/v1/sessions/{session_id}/trials`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/` | 시도 생성 |
| GET | `/{trial_id}` | 시도 상세 조회 |
| PUT | `/{trial_id}` | 시도 수정 |
| DELETE | `/{trial_id}` | 시도 삭제 |

### AI 홀드 인식 API (`/ai/v1/hold`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/sessions` | 이미지 업로드 및 세션 생성 |
| POST | `/sessions/{session_id}/holds:detect` | 좌표 기반 홀드 인식 |
| GET | `/sessions/{session_id}` | 세션 정보 조회 |
| POST | `/sessions/{session_id}:close` | 세션 종료 |

### AI 분석 API (`/ai/v1/analysis`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/jobs` | 분석 작업 생성 및 시작 |
| GET | `/jobs/{job_id}` | 작업 상태 조회 |
| GET | `/jobs/{job_id}/result` | 분석 결과 조회 |

## 아키텍처

### Backend 구조

```
src/main/java/com/ssafy/a203
├── domain/                         # 도메인 레이어
│   ├── auth/                       # 인증
│   │   ├── controller/
│   │   ├── dto/
│   │   └── service/
│   ├── user/                       # 사용자
│   │   ├── controller/
│   │   ├── dto/
│   │   ├── entity/
│   │   ├── exception/
│   │   ├── repository/
│   │   └── service/
│   ├── video/                      # 영상
│   │   ├── controller/
│   │   ├── dto/
│   │   ├── entity/
│   │   ├── exception/
│   │   ├── repository/
│   │   ├── service/
│   │   ├── _hold/                  # 홀드 인식
│   │   └── _pose/                  # 자세 분석
│   ├── exerciseSession/            # 운동 세션
│   ├── trial/                      # 운동 시도
│   └── exerciseInfo/               # 운동 정보
└── global/                         # 전역 설정
    ├── common/
    │   ├── config/                 # Redis, WebSocket, S3, Swagger 설정
    │   ├── dto/                    # 공통 응답 DTO
    │   ├── exception/              # 전역 예외
    │   ├── handler/                # 예외 핸들러
    │   └── util/                   # 유틸리티
    ├── security/                   # JWT 인증/인가
    └── validation/                 # 커스텀 검증
```

## Redis Stream 전환

### 배경: Redis Pub/Sub의 한계

기존에는 AI 서버와 Backend 간 비동기 메시지 전달에 **Redis Pub/Sub**을 사용했습니다. 하지만 다음과 같은 한계가 있었습니다:

| 문제점 | 설명 |
|--------|------|
| **메시지 유실** | Consumer가 오프라인일 때 발행된 메시지는 영구적으로 유실됨 |
| **재처리 불가** | 처리 실패한 메시지를 다시 받을 수 없음 |
| **영속성 없음** | 메시지가 메모리에만 존재하여 Redis 재시작 시 유실 |

### 해결: Redis Stream 도입

**Redis Stream**은 Kafka와 유사한 로그 기반 메시지 큐로, 다음 장점을 제공합니다:

| 장점 | 설명 |
|------|------|
| **메시지 영속성** | 메시지가 스트림에 저장되어 유실되지 않음 |
| **Consumer Group** | 여러 Consumer가 메시지를 분산 처리 가능 |
| **ACK 메커니즘** | 처리 완료 확인 후 메시지 제거 |
| **재처리 가능** | Pending 메시지를 다시 처리할 수 있음 |

### 아키텍처 변경

```
[변경 전: Pub/Sub]
AI Server → PUBLISH ai_job_result → Backend (MessageListener)
                                    ↓
                          구독 중이 아니면 메시지 유실

[변경 후: Stream]
AI Server → XADD ai_job_result_stream → Backend (@Scheduled polling)
                                         ↓
                               Consumer Group으로 메시지 관리
                               처리 완료 시 XACK
                               실패 시 Pending에서 재처리
```

### 주요 코드 변경

#### Python (AI Server) - 메시지 발행

```python
# redis_pubsub.py
class RedisPublisher:
    STREAM_NAME = "ai_job_result_stream"

    def _publish_to_stream(self, payload: dict) -> bool:
        stream_message = {
            "job_id": payload.get("job_id"),
            "eventType": "status" | "result" | "error",
            "timestamp": datetime.now().isoformat(),
            "data": json.dumps(payload)
        }
        message_id = client.xadd(self.STREAM_NAME, stream_message)
        return True
```

#### Spring Boot (Backend) - 메시지 수신

```java
// RedisStreamConfig.java
@Scheduled(fixedDelay = 500)
public void pollMessages() {
    List<MapRecord<String, Object, Object>> messages = redisTemplate.opsForStream().read(
        Consumer.from(CONSUMER_GROUP, CONSUMER_NAME),
        StreamReadOptions.empty().count(10).block(Duration.ofMillis(100)),
        StreamOffset.create(STREAM_KEY, ReadOffset.lastConsumed())
    );

    for (MapRecord<String, Object, Object> message : messages) {
        listener.onMessage(convertToStringMap(message));
    }
}
```

### 트러블슈팅

#### 1. Consumer Group 생성 실패

**문제**: 스트림이 존재하지 않을 때 `XGROUP CREATE` 명령이 실패하는데, 모든 예외를 무시하고 있었음

```java
// Before - 모든 에러를 무시
catch (Exception e) {
    log.info("Consumer group already exists");  // 실제로는 다른 에러일 수 있음
}
```

**해결**: 스트림이 없으면 먼저 생성하고, 에러 메시지를 정확히 확인

```java
// After
Boolean exists = redisTemplate.hasKey(STREAM_KEY);
if (!exists) {
    // 스트림 생성을 위해 임시 메시지 추가 후 삭제
    var messageId = redisTemplate.opsForStream().add(STREAM_KEY, Map.of("init", "true"));
    redisTemplate.opsForStream().delete(STREAM_KEY, messageId);
}

// Consumer Group 생성
try {
    redisTemplate.opsForStream().createGroup(STREAM_KEY, ReadOffset.from("0"), CONSUMER_GROUP);
} catch (Exception e) {
    if (e.getMessage().contains("BUSYGROUP")) {
        log.info("Consumer group already exists");
    } else {
        log.error("Failed to create consumer group", e);
    }
}
```

#### 2. StreamMessageListenerContainer가 동작하지 않음

**문제**: Spring Data Redis의 `StreamMessageListenerContainer`를 사용했으나, `consumers: 0`으로 실제 polling이 되지 않음

**원인 분석**:
- `container.start()` 후 `receive()` 호출 순서 문제
- Bean 생성 시점과 Container 시작 시점 불일치
- Container가 running 상태이지만 실제 XREADGROUP 미실행

**해결**: `@Scheduled` 방식으로 직접 polling 구현

```java
@Scheduled(fixedDelay = 500)
public void pollMessages() {
    if (!ready) return;

    List<MapRecord<String, Object, Object>> messages = redisTemplate.opsForStream().read(
        Consumer.from(CONSUMER_GROUP, CONSUMER_NAME),
        StreamReadOptions.empty().count(10).block(Duration.ofMillis(100)),
        StreamOffset.create(STREAM_KEY, ReadOffset.lastConsumed())
    );
    // 메시지 처리...
}
```

#### 3. Python과 Spring Boot가 서로 다른 Redis에 연결

**증상**: Python에서 메시지 발행 성공 로그가 뜨지만, Redis CLI에서 `XLEN`이 0

```bash
# Python
Published to stream 1770716547519-0: job_id=job123

# Redis CLI
127.0.0.1:6379> XLEN ai_job_result_stream
(integer) 0
```

**원인**: Windows에서 두 개의 Redis가 동시에 실행 중

```bash
# netstat 결과
TCP    0.0.0.0:6379    LISTENING    35768   # Docker Redis
TCP    127.0.0.1:6379  LISTENING    5048    # Windows 서비스 Redis
```

- Python → Docker Redis (0.0.0.0:6379)
- Spring Boot/Redis CLI → Windows Redis (127.0.0.1:6379)

**해결**: 중복 Redis 중 하나를 종료

```cmd
# 관리자 CMD에서 Windows Redis 서비스 중지
net stop Redis

# 또는 Docker Redis 컨테이너 중지
docker stop <redis_container>
```

**교훈**:
- 개발 환경에서 동일 포트를 사용하는 서비스가 중복 실행될 수 있음
- `netstat -ano | findstr :6379`로 중복 확인 필요
- Docker와 로컬 서비스를 혼용할 때 주의

### 결과

| 항목 | Before (Pub/Sub) | After (Stream) |
|------|------------------|----------------|
| 메시지 유실 | 가능 | 불가능 |
| 재처리 | 불가능 | Pending 메시지로 가능 |
| Consumer 오프라인 | 메시지 유실 | 나중에 수신 가능 |
| 모니터링 | 어려움 | XINFO, XPENDING으로 확인 |

## 환경 설정

### 필수 환경 변수

```bash
# Database
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_NAME=
POSTGRES_USERNAME=
POSTGRES_PASSWORD=

# Redis
REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=

# AWS S3
AWS_S3_BUCKET=
AWS_S3_REGION=
AWS_ACCESS_KEY=
AWS_SECRET_KEY=

# JWT
JWT_SECRET=
JWT_ACCESS_EXPIRATION=
JWT_REFRESH_EXPIRATION=

# AI Server
AI_BASE_URL=

# AI Server 환경 변수
SESS_TTL_SEC=1800
STORAGE_DIR=./storage
CORS_ALLOW_ORIGINS=*
```

## 실행 방법

### 로컬 실행

```bash
cd Backend

# 빌드
./gradlew build

# 실행
./gradlew bootRun

# 테스트 실행
./gradlew test
```

### Docker 실행

```bash
cd Backend

# Docker 이미지 빌드
docker build -t climbmate-backend .

# 컨테이너 실행
docker run -p 8080:8080 climbmate-backend
```

### AI 서버 실행

```bash
cd AI/BACKEND

# 의존성 설치
pip install -r requirement.txt

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API 문서

서버 실행 후 Swagger UI에서 API 문서를 확인할 수 있습니다.
- URL: `http://localhost:8080/swagger-ui.html`

## 테스트

### 테스트 현황

| 테스트 클래스 | 테스트 내용 |
|--------------|------------|
| AuthLoginTest | 로그인 성공/실패 |
| AuthLogoutTest | 로그아웃 |
| AuthWithdrawTest | 회원 탈퇴 |
| UserSignUpTest | 회원가입 |
| UserInformationTest | 회원 정보 조회/수정 |
| ExerciseSessionControllerTest | 세션 CRUD |
| TrialControllerTest | 시도 CRUD |
| VideoControllerTest | 영상 업로드/저장/조회 |
| VideoControllerListTest | 영상 목록 조회 |
| HoldDetectionControllerTest | 홀드 인식 |
| PoseAnalysisControllerTest | 자세 분석 작업 생성 |
| AiJobServiceTest | AI 서버 페이로드 검증 |

### 테스트 특징
- 통합 테스트 중심 (`@SpringBootTest`)
- MockMvc를 활용한 API 테스트
- MockWebServer로 외부 AI 서버 모킹
- `@Transactional`로 테스트 독립성 보장
- H2 인메모리 DB 사용

## 팀 기여 내역

이 프로젝트는 팀 프로젝트로 진행되었습니다.

### 본인 담당 영역

| 영역 | 상세 내용 |
|------|-----------|
| **Backend (Spring Boot)** | Java 백엔드 서버 전체 설계 및 구현 |
| **API 설계** | REST API 엔드포인트 설계 (인증, 사용자, 영상, 세션, 시도 등) |
| **데이터베이스 설계** | PostgreSQL 스키마 및 JPA Entity 설계 |
| **인증/인가** | Spring Security + JWT 토큰 기반 인증 시스템 구현 |
| **클라우드 연동** | AWS S3 Presigned URL 기반 영상 업로드 구현 |
| **AI 서버 연동** | AI 서버와의 REST API 통신 및 Redis Stream 기반 비동기 메시지 처리 |
| **테스트 코드** | 통합 테스트 작성 (MockMvc, MockWebServer) |
| **CI/CD** | Docker, Jenkins 기반 배포 파이프라인 구성 |

### AI 서버 담당 (팀원)

| 영역 | 상세 내용 |
|------|-----------|
| **AI 모델 개발** | YOLO11x-pose 기반 자세 추정 모델 구현 |
| **홀드 인식** | YOLOv8 커스텀 모델 기반 홀드 탐지 |
| **자세 분석 알고리즘** | 무게중심, 몸통 각도, 관절 각도 분석 로직 |
| **낙하 분석 파이프라인** | 8단계 낙하 분석 파이프라인 설계 및 구현 |
| **FastAPI 서버** | AI 분석 API 서버 구현 |

### 공동 작업 영역

| 영역 | 상세 내용 |
|------|-----------|
| **Redis Pub/Sub → Stream 전환** | 메시지 유실 방지를 위한 Redis Stream 도입 (본인 담당) |
| **메시지 프로토콜 정의** | AI 서버 ↔ Backend 간 메시지 형식 설계 |
| **시스템 아키텍처** | 전체 시스템 구성 및 통신 흐름 설계 |
