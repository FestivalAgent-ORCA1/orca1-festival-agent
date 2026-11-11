# orca1-festival-agent

축제 AI 에이전트: 취향에 맞는 축제를 추천하고, 주변 장소와 이동 시간을 계산해 하루 일정을 만들어 주는 서비스

## 구성

| 폴더 | 내용 | 기술 |
| --- | --- | --- |
| `frontend/` | 웹 화면 | React, Vite (배포: Vercel) |
| `backend/` | API 서버, AI 에이전트, 자동 실행 작업 | FastAPI, SQLAlchemy, Alembic (배포: Render) |
| `docs/` | 팀 공용 규격 문서 | [API](docs/api-spec.md) · [DB](docs/db-schema.md) · [태그](docs/tags.md) · [Tool](docs/tool-spec.md) · [채팅 응답](docs/agent-response-format.md) · [AI 흐름](docs/workflow.md) |

DB는 Aiven MySQL 공용 DB 하나를 함께 쓴다. 외부 API는 TourAPI(축제·장소), 카카오모빌리티(길찾기), Groq(AI)를 쓴다.

## 팀

| 역할 | 이름 | 브랜치 | 담당 |
| --- | --- | --- | --- |
| BE1 | 이소현 | `be1-SH` | 백엔드 총괄(기본 틀·DB·배포), 축제·장소·추천·일정 계산, AI |
| BE2 | 김민경 | `be2-MK` | 회원·찜·일정 저장·커뮤니티·알림 |
| FE1 | 김건우 | `fe1-KW` | 디자인 기준, 공통 부품, 축제 목록·상세·찜·홈 |
| FE2 | 황규원 | `fe2-GW` | AI 채팅, 일정 화면, 카카오맵 |
| FE3 | 이혜정 | `fe3-HJ` | 프론트 기본 틀, 로그인·첫 설정, 커뮤니티, 알림, 배포 |

## 실행

### 백엔드

Python 3.11을 쓴다. `backend/` 폴더에서 (PowerShell 기준):

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env   # 값은 BE1에게 비공개 채널로 받기
uvicorn app.main:app --reload
```

- API 문서: <http://localhost:8000/docs>
- 상태 확인: <http://localhost:8000/health>
- 테스트: `python -m pytest` (메모리 DB를 쓰므로 공용 DB에 영향 없음)
- 공용 DB의 테이블 변경(`alembic revision`, `alembic upgrade`)은 **BE1만** 실행한다. 모델을 바꿨다면 BE1에게 요청한다.

### 프론트엔드

[frontend/README.md](frontend/README.md) 참고. 기본은 서버 없이 도는 예시(mock) 모드이고, 백엔드와 연결하려면 `frontend/.env`에 아래를 넣는다.

```ini
VITE_DATA_MODE=api
VITE_API_BASE_URL=http://localhost:8000
```

## 작업 규칙

1. 각자 브랜치에서 작업하고, PR은 **`develop`** 으로 올린다 (`main` 아님)
2. 리뷰 승인 후 병합. `main`에는 BE1이 develop을 확인한 뒤 올린다
3. 최신 develop 받기: `git fetch origin` → `git merge origin/develop --no-edit` → `git push`
4. API·DB 규격을 바꿀 때는 `docs/`를 먼저 고치고 관련 담당자를 리뷰어로 넣는다
5. `.env`, API 키, `backend/certs/`는 깃에 올리지 않는다
