# DB 테이블 구조

> 담당: BE1(축제 관련 테이블) · BE2(사용자 데이터 테이블) · 상태: **초안**
>
> 테이블을 바꾸려면 **이 문서를 먼저 고치고** → 모델 수정 → Alembic 마이그레이션 순서로 진행합니다.

## 공통 규칙

- MySQL 8, 문자셋 `utf8mb4` / `utf8mb4_unicode_ci` (한글·이모지)
- 테이블·컬럼 이름은 `snake_case`, 테이블 이름은 복수형
- 모든 테이블에 `created_at`, 수정되는 테이블에는 `updated_at` (DATETIME)
- **시간은 모두 한국 시간(Asia/Seoul) 기준으로 저장**. 국내 전용 서비스라 시간대 변환을 하지 않음
- 축제·장소 ID는 TourAPI `contentId`를 그대로 쓰고 **문자열**(`VARCHAR(20)`)로 저장
- 삭제: 사용자가 탈퇴하면 그 사용자의 찜·일정·알림은 함께 삭제(`ON DELETE CASCADE`), 게시글·댓글은 1차 범위에서 함께 삭제

### Alembic 사용 규칙

1. 마이그레이션을 만들기 전에 반드시 `develop`을 최신으로 받기
2. `alembic heads` 결과가 1개인지 확인한 뒤 `alembic revision --autogenerate -m "설명"`
3. 자동 생성 파일은 꼭 열어서 확인 (autogenerate가 놓치는 것: 컬럼 이름 변경, 일부 인덱스)
4. 같은 날 BE1·BE2가 둘 다 마이그레이션을 만들면 PR 머지 전에 서로 알리기

---

## 테이블 목록

| 테이블 | 담당 | 모델 파일 |
| --- | --- | --- |
| `users`, `user_regions`, `user_tags` | BE2 | `models/user.py` |
| `festivals`, `festival_tags`, `travel_times` | BE1 | `models/festival.py` |
| `likes` | BE2 | `models/like.py` |
| `schedules`, `schedule_items` | BE2 | `models/schedule.py` |
| `posts`, `comments` | BE2 | `models/post.py` |
| `notifications` | BE2 | `models/notification.py` |

---

## users — 회원

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | BIGINT PK AUTO_INCREMENT | |
| `email` | VARCHAR(255) UNIQUE NOT NULL | 로그인 ID |
| `password_hash` | VARCHAR(255) NOT NULL | bcrypt 해시. 원문 비밀번호는 절대 저장·로그 출력 금지 |
| `nickname` | VARCHAR(30) NOT NULL | |
| `age_group` | VARCHAR(10) NULL | [tags.md](tags.md) 연령대 코드. 온보딩 전에는 NULL |
| `onboarded` | BOOLEAN NOT NULL DEFAULT FALSE | 첫 설정 완료 여부 |
| `created_at` / `updated_at` | DATETIME | |

## user_regions — 선호 지역 (0~3개)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `user_id` | BIGINT FK → users.id | PK (user_id, area_code) |
| `area_code` | VARCHAR(5) | [tags.md](tags.md) 지역 코드 |

## user_tags — 관심사 (1~5개)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `user_id` | BIGINT FK → users.id | PK (user_id, tag_code) |
| `tag_code` | VARCHAR(20) | [tags.md](tags.md) 태그 코드 |

---

## festivals — 축제 (TourAPI 동기화)

`batch/sync_festivals.py`가 주 1회 채움. 목록 화면·추천·AI 검색은 모두 이 테이블을 조회합니다.

| 컬럼 | 타입 | 설명 / TourAPI 필드 |
| --- | --- | --- |
| `content_id` | VARCHAR(20) PK | `contentid` |
| `title` | VARCHAR(200) NOT NULL | `title` |
| `start_date` | DATE NOT NULL | `eventstartdate` (YYYYMMDD → DATE 변환) |
| `end_date` | DATE NOT NULL | `eventenddate` |
| `area_code` | VARCHAR(5) NULL | `areacode` |
| `sigungu_code` | VARCHAR(5) NULL | `sigungucode` |
| `address` | VARCHAR(300) NULL | `addr1` + `addr2` |
| `lng` | DECIMAL(10,7) NULL | `mapx` (경도) |
| `lat` | DECIMAL(10,7) NULL | `mapy` (위도) |
| `image_url` | VARCHAR(500) NULL | `firstimage` |
| `thumbnail_url` | VARCHAR(500) NULL | `firstimage2` |
| `tel` | VARCHAR(100) NULL | `tel` |
| `overview` | TEXT NULL | 상세(`detailCommon2`) — 태그 추출에 사용 |
| `homepage` | VARCHAR(1000) NULL | 상세. HTML 태그가 섞여 오므로 저장 전 정리 |
| `place` | VARCHAR(300) NULL | 소개(`detailIntro2`) `eventplace` |
| `playtime` | VARCHAR(300) NULL | 소개 `playtime` (자유 형식 문자열) |
| `fee` | VARCHAR(500) NULL | 소개 `usetimefestival` |
| `tourapi_modified_at` | DATETIME NULL | `modifiedtime` — 바뀐 축제만 상세를 다시 받기 위해 |
| `detail_synced_at` | DATETIME NULL | 상세·소개를 마지막으로 받은 시각 |
| `created_at` / `updated_at` | DATETIME | |

인덱스: `(start_date, end_date)`, `(area_code)`

## festival_tags — 축제 태그 (1~3개)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `content_id` | VARCHAR(20) FK → festivals.content_id | PK (content_id, tag_code) |
| `tag_code` | VARCHAR(20) | |

## travel_times — 이동 시간 캐시

카카오 길찾기 호출을 줄이기 위해 한 번 계산한 두 장소 사이 결과를 저장합니다.

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `from_content_id` | VARCHAR(20) | PK (from_content_id, to_content_id) |
| `to_content_id` | VARCHAR(20) | 방향이 있음 (A→B와 B→A는 따로 저장) |
| `duration_min` | INT NOT NULL | 자동차 기준 분 |
| `distance_km` | DECIMAL(6,2) NOT NULL | |
| `created_at` | DATETIME | 30일이 지난 값은 다시 계산 |

> 주변 장소(관광지·음식점)는 따로 테이블에 저장하지 않고 요청할 때 TourAPI로 조회합니다.
> 일정에 들어간 장소 정보는 `schedule_items`에 복사해서 저장합니다.

---

## likes — 찜

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | BIGINT PK | |
| `user_id` | BIGINT FK → users.id | |
| `content_id` | VARCHAR(20) FK → festivals.content_id | |
| `created_at` | DATETIME | |

UNIQUE `(user_id, content_id)` — 같은 축제를 두 번 찜하지 않음

---

## schedules — 저장한 일정

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | BIGINT PK | |
| `user_id` | BIGINT FK → users.id | |
| `festival_content_id` | VARCHAR(20) FK → festivals.content_id | 중심 축제 |
| `title` | VARCHAR(100) NOT NULL | 기본값: "{축제명} 일정" |
| `visit_date` | DATE NOT NULL | |
| `start_time` | TIME NOT NULL | 일정 시작 |
| `end_time` | TIME NOT NULL | 일정 종료 |
| `total_travel_min` | INT NOT NULL DEFAULT 0 | |
| `created_at` / `updated_at` | DATETIME | |

## schedule_items — 일정 안의 장소 (시간표 한 줄)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | BIGINT PK | |
| `schedule_id` | BIGINT FK → schedules.id ON DELETE CASCADE | |
| `seq` | INT NOT NULL | 방문 순서 (1부터) |
| `category` | VARCHAR(20) NOT NULL | `festival` / `attraction` / `restaurant` / `cafe` |
| `content_id` | VARCHAR(20) NULL | TourAPI ID (사용자가 직접 넣은 장소면 NULL) |
| `name` | VARCHAR(200) NOT NULL | |
| `address` | VARCHAR(300) NULL | |
| `lng` / `lat` | DECIMAL(10,7) NULL | 지도 표시용 |
| `start_time` / `end_time` | TIME NOT NULL | |
| `travel_min_from_prev` | INT NULL | 이전 장소에서 오는 시간. 첫 장소는 NULL |
| `distance_km_from_prev` | DECIMAL(6,2) NULL | |
| `memo` | VARCHAR(300) NULL | |

UNIQUE `(schedule_id, seq)`

---

## posts — 게시글

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | BIGINT PK | |
| `user_id` | BIGINT FK → users.id | |
| `festival_content_id` | VARCHAR(20) NULL FK → festivals.content_id | 관련 축제 (선택) |
| `title` | VARCHAR(100) NOT NULL | |
| `content` | TEXT NOT NULL | |
| `view_count` | INT NOT NULL DEFAULT 0 | |
| `created_at` / `updated_at` | DATETIME | |

## comments — 댓글

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | BIGINT PK | |
| `post_id` | BIGINT FK → posts.id ON DELETE CASCADE | |
| `user_id` | BIGINT FK → users.id | |
| `content` | VARCHAR(1000) NOT NULL | |
| `created_at` / `updated_at` | DATETIME | |

---

## notifications — 알림

`batch/send_notifications.py`가 매일 오전에 만듭니다.

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | BIGINT PK | |
| `user_id` | BIGINT FK → users.id | |
| `type` | VARCHAR(30) NOT NULL | `FESTIVAL_D7` / `FESTIVAL_D1` / `FESTIVAL_START` / `SIMILAR_FESTIVAL` |
| `festival_content_id` | VARCHAR(20) NULL FK → festivals.content_id | 누르면 이동할 축제 |
| `message` | VARCHAR(300) NOT NULL | 화면에 보여줄 문장 |
| `is_read` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `created_at` | DATETIME | |

UNIQUE `(user_id, type, festival_content_id)` — 배치가 두 번 돌아도 같은 알림이 중복 생성되지 않게
