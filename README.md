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
└── README.md                  # 프로젝트 문서
```

## 기술 스택

### Backend
| 분류 | 기술 |
|------|------|
| **Framework** | Spring Boot 3.5.7 |
| **Security** | Spring Security + JWT |
| **Database** | PostgreSQL, Redis |
| **ORM** | Spring Data JPA |
| **Cloud Storage** | AWS S3 |
| **Real-time** | WebSocket (STOMP), Redis Pub/Sub |
| **API Docs** | SpringDoc OpenAPI (Swagger) |
| **Build** | Gradle |
| **Containerization** | Docker |

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
- WebSocket + Redis Pub/Sub 실시간 결과 전송
- 비동기 분석 작업 큐 관리

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
