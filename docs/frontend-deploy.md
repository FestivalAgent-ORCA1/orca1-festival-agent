# 프론트 배포 (Vercel)

> 담당: FE3 · 상태: **배포됨 · API 모드** (2026-11-22 기준)

## 배포 주소

**https://orca1-festival-agent.vercel.app**

- 2026-11-22에 주소에서 `-frontend`를 뺀 새 주소를 추가했습니다 (Vercel **Settings → Environments → Production → Domains**). 카카오 Web 도메인(FE2)과 백엔드 `CORS_ORIGINS`(BE1)에도 새 주소가 등록되어 있습니다.
- 예전 주소 `https://orca1-festival-agent-frontend.vercel.app`도 같은 사이트로 계속 열립니다. 공유할 때는 새 주소를 써 주세요.

- **`develop` 브랜치**를 배포하고, Render 백엔드(`https://orca1-festival-agent.onrender.com`)의 실제 데이터를 씁니다.
- `develop`에 머지될 때마다 자동으로 다시 배포됩니다.
- Render 무료 서버는 한동안 요청이 없으면 잠들어서, **첫 요청은 1분 가까이 걸릴 수 있습니다** (`api/client.js`의 제한 시간 90초).

## 현재 상태

| 단계 | 담당 | 상태 |
| --- | --- | --- |
| 배포 설정 파일 (`frontend/vercel.json`) | FE3 | ✅ 완료 (PR #7) |
| Vercel GitHub 앱 조직 설치 | BE1 | ✅ 완료 (orca1-festival-agent 저장소) |
| Vercel 프로젝트 연결 (FE3 개인 Hobby 계정) | FE3 | ✅ 완료 |
| 예시 모드 배포 | FE3 | ✅ 완료 (11/18) |
| 백엔드 Render 배포 → 주소 공유 | BE1 | ✅ 완료 |
| 백엔드 `CORS_ORIGINS`에 Vercel·로컬 주소 허용 | BE1 | ✅ 확인 (11/19, Vercel 주소·`127.0.0.1:5173`·`localhost:5173` 사전 요청 통과) |
| Vercel 환경 변수(`VITE_DATA_MODE=api`, `VITE_API_BASE_URL`) 입력 → 다시 배포 | FE3 | ✅ 완료 (11/19) |
| 카카오 JavaScript SDK 도메인에 위 배포 주소 등록 | FE2 | ✅ 완료 (11/19) |
| Vercel 환경 변수 `VITE_KAKAO_MAP_KEY` 입력 → 다시 배포 | FE3 | ✅ 완료 (11/19, FE2에게 키 받음) |

## 구조

- Vercel 프로젝트 `orca1-festival-agent-frontend` 하나가 이 저장소의 `frontend/` 폴더를 배포합니다. FE3(이혜정)의 개인 Hobby 계정에 있습니다.
- **Production 브랜치는 `develop`** 입니다. 구축 기획서에는 배포 브랜치가 `main`이라고 되어 있지만, 서비스를 Aiven 무료 플랜 종료(2026-12-21)와 함께 끝내기로 해서 **끝까지 `develop`으로 배포**합니다. Render 백엔드도 `develop`입니다 (2026-11-19 결정). `main`에는 마지막에 최종 코드만 남기므로, Vercel **Branch Tracking**을 `main`으로 바꾸지 않습니다.
- 다른 브랜치에 push하면 Vercel이 **미리 보기(Preview) 주소**를 따로 만듭니다 (Deployments 탭). 다른 팀원이 push한 커밋도 자동 배포되는 것을 확인했습니다.
- 조직의 **public** 저장소라 Hobby(무료) 플랜으로 배포할 수 있습니다. 저장소를 private으로 바꾸면 Hobby로는 배포할 수 없으니 주의해 주세요 ([Vercel 문서](https://vercel.com/docs/git)).

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
