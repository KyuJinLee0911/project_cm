# ClimbMate Backend

실내 스포츠 클라이밍 운동 영상을 AI로 분석하는 플랫폼의 Java 백엔드 서버입니다.

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | ClimbMate |
| **설명** | 클라이밍 운동 영상의 AI 기반 자세 분석 및 홀드 인식 플랫폼 |
| **Java 버전** | 17 |
| **Spring Boot** | 3.5.7 |
| **빌드 도구** | Gradle |

## 프로젝트 규모

| 분류 | 개수 |
|------|------|
| **총 Java 파일** | 135개 |
| ├ Main 소스 | 120개 |
| └ Test 소스 | 15개 |
| **테스트 메서드** | **24개** (통합 테스트) |
| **API 엔드포인트** | 26개 |
| **컨트롤러** | 8개 |
| **서비스** | 12개 |
| **레포지토리** | 6개 |
| **엔티티** | 7개 |
| **DTO 클래스** | 33개 |

## 기술 스택

### Core
- Spring Boot 3.5.7
- Spring Security + JWT
- Spring Data JPA
- Spring WebFlux

### Database
- PostgreSQL
- Redis (토큰 관리 & Stream)

### Cloud & Storage
- AWS S3 (영상/이미지 저장)
- Spring Cloud AWS 3.3.0

### Real-time
- WebSocket (STOMP)
- Redis Stream (AI 서버 ↔ Backend 비동기 메시지)

### Documentation
- SpringDoc OpenAPI (Swagger UI)

### Testing
- JUnit 5
- Mockito
- MockWebServer
- H2 Database

## 프로젝트 구조

```
src/main/java/com/ssafy/a203
├── domain/
│   ├── auth/                    # 인증 (로그인/로그아웃/토큰 재발급)
│   ├── user/                    # 사용자 관리
│   ├── video/                   # 영상 관리
│   │   ├── _hold/               # AI 홀드 인식
│   │   └── _pose/               # AI 자세 분석
│   ├── exerciseSession/         # 운동 세션
│   ├── trial/                   # 운동 시도
│   ├── exerciseInfo/            # 운동 정보
│   └── redis/                   # Redis 테스트
└── global/
    ├── common/
    │   ├── config/              # Redis, WebSocket, S3, Swagger 설정
    │   ├── dto/                 # 공통 응답 DTO
    │   ├── exception/           # 전역 예외
    │   ├── handler/             # 예외 핸들러
    │   └── util/                # 유틸리티 (S3, JSON)
    ├── security/                # JWT 인증/인가
    └── validation/              # 커스텀 검증
```

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
- 클라이밍 홀드(손잡이) 자동 인식
- 홀드 좌표, 타입, 폴리곤 정보 저장
- 실시간 세션 기반 인식 프로세스

### 5. AI 자세 분석
- 운동 영상 기반 자세 분석
- WebSocket + Redis Stream 실시간 결과 전송
- 비동기 분석 작업 큐 관리

### 6. Redis Stream 기반 AI 서버 연동
- **Consumer Group** 기반 메시지 관리
- **@Scheduled polling** 방식으로 메시지 수신 (500ms 간격)
- **ACK 메커니즘**으로 처리 완료 확인
- **Pending 메시지 재처리** 지원

## API 엔드포인트

### 인증 API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/auth/login` | 로그인 |
| POST | `/api/v1/auth/logout` | 로그아웃 |
| POST | `/api/v1/auth/reissue` | 토큰 재발급 |

### 사용자 API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/users` | 회원가입 |
| GET | `/api/v1/users` | 회원 정보 조회 |
| PUT | `/api/v1/users` | 회원 정보 수정 |
| GET | `/api/v1/users/email` | 이메일 중복 확인 |
| DELETE | `/api/v1/users` | 회원 탈퇴 |

### 영상 API
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/videos/pre-signed` | 업로드 URL 요청 |
| POST | `/api/v1/videos` | 영상 정보 등록 |
| GET | `/api/v1/videos` | 영상 목록 조회 |
| GET | `/api/v1/videos/{video_id}` | 영상 상세 조회 |

### 홀드 인식 API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/videos/{video_id}/holds/detect/open` | 홀드 인식 세션 시작 |
| POST | `/api/v1/videos/{video_id}/holds/detect` | 홀드 인식 요청 |
| DELETE | `/api/v1/videos/{video_id}/holds/detect/{hold_id}` | 홀드 삭제 |

### 자세 분석 API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/videos/{video_id}/analysis` | 자세 분석 요청 |
| GET | `/api/v1/videos/{video_id}/analysis` | 분석 결과 조회 |

### 운동 세션 API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/sessions` | 세션 생성 |
| GET | `/api/v1/sessions` | 세션 목록 조회 |
| GET | `/api/v1/sessions/{session_id}` | 세션 상세 조회 |
| PUT | `/api/v1/sessions/{session_id}` | 세션 종료 |
| DELETE | `/api/v1/sessions/{session_id}` | 세션 삭제 |

### 운동 시도 API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/sessions/{session_id}/trials` | 시도 생성 |
| GET | `/api/v1/sessions/{session_id}/trials/{trial_id}` | 시도 상세 조회 |
| PUT | `/api/v1/sessions/{session_id}/trials/{trial_id}` | 시도 수정 |
| DELETE | `/api/v1/sessions/{session_id}/trials/{trial_id}` | 시도 삭제 |

## 테스트 현황

### 테스트 메서드 상세 (총 24개)

| 테스트 클래스 | 메서드 수 | 테스트 내용 |
|--------------|----------|------------|
| AuthLoginTest | 2 | 로그인 성공/실패 |
| AuthLogoutTest | 1 | 로그아웃 |
| AuthWithdrawTest | 1 | 회원 탈퇴 |
| UserSignUpTest | 1 | 회원가입 |
| UserInformationTest | 2 | 회원 정보 조회/수정 |
| ExerciseSessionControllerTest | 5 | 세션 CRUD |
| TrialControllerTest | 4 | 시도 CRUD |
| VideoControllerTest | 3 | 영상 업로드/저장/조회 |
| VideoControllerListTest | 2 | 영상 목록 조회 |
| HoldDetectionControllerTest | 1 | 홀드 인식 |
| PoseAnalysisControllerTest | 1 | 자세 분석 작업 생성 |
| AiJobServiceTest | 1 | AI 서버 페이로드 검증 |

### 테스트 특징
- **통합 테스트** 중심 (`@SpringBootTest`)
- MockMvc를 활용한 API 테스트
- MockWebServer로 외부 AI 서버 모킹
- `@Transactional`로 테스트 독립성 보장

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
```

## 실행 방법

```bash
# 빌드
./gradlew build

# 실행
./gradlew bootRun

# 테스트 실행
./gradlew test
```

## API 문서

서버 실행 후 Swagger UI에서 API 문서를 확인할 수 있습니다.
- URL: `http://localhost:8080/swagger-ui.html`

## Redis Stream 연동

### 아키텍처

```
AI Server (Python)                    Backend (Spring Boot)
       │                                      │
       │  XADD ai_job_result_stream           │
       ├─────────────────────────────────────→│
       │                                      │ @Scheduled polling (500ms)
       │                                      │ XREADGROUP
       │                                      │ 메시지 처리
       │                                      │ XACK
```

### 주요 컴포넌트

| 클래스 | 역할 |
|--------|------|
| `RedisStreamConfig` | Stream polling 및 Consumer Group 관리 |
| `AiJobStreamListener` | 메시지 처리 및 WebSocket 전송 |

### 메시지 형식

```json
{
  "job_id": "uuid",
  "eventType": "status | result | error",
  "timestamp": "2024-01-01T12:00:00",
  "data": "{...}"
}
```

### Redis Stream vs Pub/Sub

| 항목 | Pub/Sub (이전) | Stream (현재) |
|------|----------------|---------------|
| 메시지 영속성 | 없음 | 있음 |
| Consumer 오프라인 | 메시지 유실 | 나중에 수신 가능 |
| 재처리 | 불가능 | Pending에서 재처리 |
| ACK | 없음 | 지원 |
