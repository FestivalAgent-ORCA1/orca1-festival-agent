# 2026-11-13 · FE3 커뮤니티·내 정보·알림함·배포 설정

지난 작업: [2026-11-08-fe3-auth.md](2026-11-08-fe3-auth.md)

## 진행 순서

1. develop 받기. FE2(PR #3)와 `router/index.jsx`, `api/repository.js`가 충돌해서 양쪽 줄을 모두 남기는 방식으로 해결했습니다. FE2 쪽에 있던 `/login` 임시 화면 줄은 진짜 로그인 페이지로 대체했습니다.
2. PR #4(로그인·첫 설정·하단 메뉴) BE1 승인 후 develop에 머지.
3. 아래 기능을 새 PR로 올림.

## 추가한 것

### 커뮤니티 (api-spec 10장)

| 주소 | 내용 |
| --- | --- |
| `/community` | 글 목록 (10개씩 페이지), `?festival=<content_id>`면 그 축제 글만 |
| `/community/:id` | 글 상세, 댓글, 내 글이면 수정·삭제 (삭제는 한 번 더 확인) |
| `/community/write` | 새 글. `?festival=`로 들어오면 관련 축제가 자동 연결됨 |
| `/community/:id/edit` | 수정. 상세에서 글 데이터를 넘겨받아 조회수가 또 오르지 않게 함 |

- 부품: `PostItem`, `CommentList`, `PostEditor` (`components/community/`)
- `api/posts.js`, 예시 모드용 `api/demoCommunity.js` (예시 글 2개·댓글 1개)
- PC 헤더에 **커뮤니티** 버튼 추가 (620px 이하는 하단 메뉴로)

### 내 정보 `/profile`

- 닉네임·이메일·가입일, 바로 가기(나의 티켓·내 일정·알림함·커뮤니티)
- 닉네임 수정, 취향 보기 → **바꾸기**는 `/onboarding?redirect=/profile` 재사용 (이미 설정한 사용자에게는 버튼이 "저장하기")
- 로그아웃, 회원 탈퇴(한 번 더 확인)
- 로그인 상태의 PC 헤더 버튼을 **로그아웃 → 내 정보**로 변경

### 알림함 `/notifications` (api-spec 11장)

- 목록, 누르면 읽음 처리 후 축제 상세로 이동, **모두 읽음**
- `contexts/NotificationsContext.jsx`: 안 읽은 수를 페이지 이동마다 다시 확인 → PC 헤더 **내 정보** 숫자, 하단 메뉴 점, 내 정보의 알림함 링크
- 예시 모드: 계정마다 예시 알림 3개 (`api/demoNotifications.js`)

### 배포 설정

- `frontend/vercel.json`에 빌드 방법(Vite·pnpm·dist) 명시
- [frontend-deploy.md](frontend-deploy.md): Vercel 설정값, 환경 변수, BE·FE2에 부탁할 것

## 검증

- 자동 테스트 35개 통과 (`tests/community.test.js` 3개, `tests/notifications.test.js` 2개 추가)
- `pnpm build` 성공
- 브라우저(예시 모드): 글쓰기·수정·삭제, 댓글 쓰기·삭제, 닉네임·취향 수정, 로그아웃, 알림 읽음·모두 읽음·배지 확인
- 참고: 개발 서버(StrictMode)에서는 글 조회수가 2씩 오를 수 있음. 배포 빌드에서는 1씩

## 남은 일

- **실제 백엔드 연동 확인**: 지금까지는 예시 모드로만 확인. `backend/app/main.py`가 아직 비어 있어 Render 주소가 없음 (BE1). 서버가 뜨면 `VITE_DATA_MODE=api`로 가입부터 알림까지 한 번 확인
- **Vercel 연결**: 누구 계정에 만들지, 조직 저장소 접근 승인 → 팀에 질문함
- 백엔드 CORS에 Vercel 주소 추가 (BE), 카카오 JavaScript SDK 도메인 등록 (FE2)
- PC 헤더 버튼이 7개라 태블릿 폭(621~1050px)에서 넘치는지 확인 필요
- FE1 참고: 축제 상세에 `/community?festival=<content_id>` 링크를 달면 그 축제 이야기로 바로 연결됨
