# 프론트 배포 (Vercel)

> 담당: FE3 · 상태: **초안** (백엔드 Render 주소가 정해지면 갱신)

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

- **BE1/BE2**: 백엔드 CORS 허용 목록에 Vercel 주소(Production + develop 미리 보기)를 추가해 주세요. `localhost`와 `127.0.0.1`처럼 주소가 조금만 달라도 다른 출처입니다.
- **FE2**: 카카오 개발자 콘솔의 JavaScript SDK 도메인에 Vercel 주소를 등록해 주세요.

## 새로고침 404 방지

`vercel.json`의 `rewrites`가 `/community/12` 같은 주소를 새로고침해도 `index.html`을 돌려줘서 React 라우터가 화면을 그립니다. `assets/`와 `api/`로 시작하는 주소는 제외합니다.
