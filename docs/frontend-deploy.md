# 프론트 배포 (Vercel)

> 담당: FE3 · 상태: **배포 전** (2026-11-14 기준)

## 현재 상태

> ⚠️ **아직 Vercel에 배포하지 않았습니다.** 지금 있는 것은 배포 **설정 파일**(`frontend/vercel.json`)과 이 안내 문서뿐이고, 배포 주소는 아직 없습니다.

| 단계 | 담당 | 상태 |
| --- | --- | --- |
| 배포 설정 파일 (`frontend/vercel.json`) | FE3 | ✅ 완료 (PR #7) |
| 백엔드 Render 배포 → 주소 공유 | BE1 | ⏳ 대기 |
| Vercel 프로젝트를 만들 계정 정하기, 조직 저장소 접근 승인 | 팀 | ⏳ 결정 필요 |
| Vercel 프로젝트 연결 + 환경 변수 입력 | FE3 | ⏳ 위 두 단계 후 |
| 백엔드 `CORS_ORIGINS`에 Vercel 주소 추가 | BE1 | ⏳ Vercel 주소가 나온 후 |
| 카카오 JavaScript SDK 도메인 등록 | FE2 | ⏳ Vercel 주소가 나온 후 |

배포하면 이 표와 아래 "배포 주소"를 갱신합니다.

### 배포 주소

- Production (`main`): 아직 없음
- develop 미리 보기: 아직 없음

## 구조

- Vercel 프로젝트 하나가 이 저장소의 `frontend/` 폴더를 배포합니다.
- **Production 브랜치는 `main`** 입니다. 구축 기획서대로 `main`은 BE1이 develop을 확인한 뒤 올립니다.
- Vercel은 다른 브랜치에 push할 때마다 **미리 보기(Preview) 주소**를 따로 만듭니다. 팀 확인은 `develop`의 미리 보기 주소로 합니다.

## Vercel 프로젝트 설정 (처음 한 번)

| 항목 | 값 |
| --- | --- |
| Root Directory | `frontend` |
| Framework / Install / Build / Output | `frontend/vercel.json`에 적혀 있어 따로 입력하지 않아도 됩니다 (Vite, `pnpm install --frozen-lockfile`, `pnpm build`, `dist`) |
| Node.js Version | 22.x 이상 (`package.json`의 `engines`) |

### 환경 변수 (Settings → Environment Variables)

| 이름 | 값 | 비고 |
| --- | --- | --- |
| `VITE_DATA_MODE` | `api` | 백엔드가 준비되기 전에는 넣지 않으면 예시(mock) 모드로 뜹니다 |
| `VITE_API_BASE_URL` | `https://<Render 주소>.onrender.com` | `/api`를 붙이지 않습니다 |
| `VITE_KAKAO_MAP_KEY` | 카카오 JavaScript 키 | FE2 지도. 비워 두면 지도 대신 순서 그림 |

- `VITE_` 변수는 브라우저에 그대로 공개됩니다. 비밀번호·서버 키를 넣지 않습니다.
- 환경 변수를 바꾼 뒤에는 **Redeploy**해야 반영됩니다 (빌드할 때 코드에 박히는 값이라서).

## 배포 후 다른 담당에게 알릴 것

- **BE1**: Render 환경 변수 `CORS_ORIGINS`(쉼표로 여러 개, `backend/app/core/config.py`)에 Vercel 주소(Production + develop 미리 보기)를 추가해 주세요. 끝에 `/`는 붙이지 않습니다.
  - 로컬 확인용: 프론트 개발 서버는 `http://127.0.0.1:5173`으로 뜹니다(`package.json`의 `vite --host 127.0.0.1`). 백엔드 기본값은 `http://localhost:5173`뿐이라, 로컬에서 api 모드로 붙일 때는 `CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`이 필요합니다. `localhost`와 `127.0.0.1`은 서로 다른 출처입니다.
- **FE2**: 카카오 개발자 콘솔의 JavaScript SDK 도메인에 Vercel 주소를 등록해 주세요.

## 새로고침 404 방지

`vercel.json`의 `rewrites`가 `/community/12` 같은 주소를 새로고침해도 `index.html`을 돌려줘서 React 라우터가 화면을 그립니다. `assets/`와 `api/`로 시작하는 주소는 제외합니다.
