# ORCA 프론트엔드 · FE1

‘주말의 입장권’ 디자인을 React 화면과 재사용 부품으로 구현했습니다. 기존 저장소의 프론트 파일이 빈 상태여서 실행에 필요한 최소 진입점과 라우터도 함께 작성했습니다. 이 공통 부분은 FE3와 함께 검토해 주세요.

[팀 Figma의 PC·모바일 화면과 공통 컴포넌트](https://www.figma.com/design/XVAdqmWomFrfhcp54p0VDI/ORCA-festival?node-id=25-240)와 [2026-11-06 팀 검토 안내](../docs/2026-11-06-fe1-review.md)를 함께 확인할 수 있습니다.

## 실행

Node.js 22.12 이상과 pnpm 11.25.0을 사용합니다.

```sh
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

터미널에 나온 주소를 브라우저에서 엽니다. 기본 데이터 모드는 `mock`이므로 서버 없이 화면을 확인할 수 있습니다.

```sh
pnpm test
pnpm build
pnpm preview
```

## 구현한 화면과 동작

| 경로                    | 내용                                                           |
| ----------------------- | -------------------------------------------------------------- |
| `/`                     | 홈, 축제 검색, 찜 요약. 로그인한 API 사용자에게 맞춤 추천 표시 |
| `/festivals`            | 지역·이름·분위기 필터, 정렬, 페이지 이동                       |
| `/festivals/:contentId` | 상세 정보, 공식 안내, 찜, 비슷한 축제                          |
| `/likes`                | 저장한 축제와 찜 해제                                          |

사진의 미리 보기 팝업, Escape로 닫기, 다음 축제 보기, 버튼 눌림, 찜을 담을 때의 작은 폭죽, 모션 줄이기 설정을 지원합니다. 홈·목록·상세·팝업·찜 목록은 동일한 찜 상태를 공유합니다. 작은 화면의 주요 버튼은 44px 이상입니다.

## 서버 연결

`.env.example`을 `.env`로 복사한 뒤 아래처럼 설정하고 개발 서버를 다시 실행합니다.

```dotenv
VITE_DATA_MODE=api
VITE_API_BASE_URL=http://localhost:8000
```

- 주소에는 `/api`를 붙이지 않습니다. 같은 도메인 프록시를 쓰면 빈 값도 가능합니다.
- `VITE_` 변수는 브라우저에 공개됩니다. 비밀번호나 서비스 비밀 키를 넣지 않습니다.
- API는 [develop의 api-spec.md](https://github.com/FestivalAgent-ORCA1/orca1-festival-agent/blob/develop/docs/api-spec.md)를 따릅니다. `content_id`, `area_code`, `is_liked` 등 snake_case를 유지합니다.
- `api/client.js`는 요청 취소·시간 제한·서버 오류를 처리합니다. 기획서의 Render 첫 응답 대기를 고려해 기본 제한은 90초이며, 클라이언트를 만들 때 `timeoutMs`로 바꿀 수 있습니다. 서버 모드의 실패를 예시 데이터로 바꾸지 않습니다.
- 찜 POST가 성공해야 저장 상태를 바꿉니다. 본문 없는 성공 응답과 `409 ALREADY_LIKED`는 저장 성공으로 처리하고, 이외 오류는 기존 상태를 유지합니다. 목록의 빈 응답이나 잘못된 JSON은 오류로 처리합니다. 중복 클릭은 요청 중 잠급니다.
- 내 찜 목록이 50개보다 많으면 뒤 페이지까지 읽습니다.
- 백엔드의 CORS에는 실제 프론트 주소를 허용해야 합니다. `localhost`와 `127.0.0.1`은 서로 다른 출처입니다.

### FE3에게 연결을 부탁할 부분

1. `router/index.jsx`의 `/login`을 실제 `LoginPage`로 교체합니다. 현재는 ‘로그인 화면 준비 중’ 안내만 있으며 로그인 구현을 대신하지 않습니다.
2. 인증 컨텍스트를 만든 뒤 `api/repository.js`의 `getAccessToken()`과 맞춥니다. 현재 계약은 `localStorage.access_token`입니다. 로그인·로그아웃 후 `window.dispatchEvent(new Event('orca:auth-changed'))`를 보내면 찜 상태를 다시 읽습니다. 같은 키의 다른 탭 변경도 감지합니다.
3. 서버의 401 응답은 토큰을 비우고 `/login?redirect=...`로 이동합니다. 로그인 완료 후 복귀 주소는 내부 경로만 허용해 주세요.
4. 공통 Header·PageLayout·App·라우터의 최소 실행 코드를 FE3의 구조에 합칩니다. 다른 담당의 로그인·채팅·커뮤니티·일정 페이지는 구현하지 않았습니다.

로그인한 사용자만 `/api/festivals/recommended`를 호출합니다. 비로그인 사용자에게 개인화된 추천인 것처럼 표시하지 않습니다.

### FE2 지원 부품

`components/schedule/PlacePicker.jsx`는 `festivalContentId`, `selectedIds`, `onAdd(place)`, `onRemove(contentId)`를 받습니다. API 모드에서 `/api/places/nearby`를 호출해 관광지·음식점·카페와 페이지 이동을 표시합니다. 부모가 선택 상태와 일정 계산을 관리합니다. FE2의 일정 화면에는 아직 삽입하지 않았습니다.

## 예시 모드의 범위

- 공식 자료를 참고한 2026년 11월 축제 3곳을 고정 데이터로 제공합니다. 날짜가 바뀌어도 검토할 수 있는 예시이며, 최신 전국 축제 목록이 아닙니다.
- ID는 `demo-` 접두어를 사용하며 실제 TourAPI ID가 아닙니다. API 모드와 저장을 분리해 예시 ID를 서버로 전송하지 않습니다.
- 찜은 `orca:demo:likes:v1` 키로 브라우저에 저장합니다. 저장소 접근이 막히면 메모리에서 동작하고 저장 제한을 알립니다.
- 예시 모드에서는 계정 로그인·맞춤 추천·주변 장소·예매·결제가 이루어지지 않습니다.

## 검증과 남은 연동

- 자동 테스트: 실제 로컬 HTTP 요청의 필터·JWT·본문 형식, 취소·시간 제한, 401, 중복 찜, 여러 페이지의 찜 목록, 검색·날짜 필터, 저장 복원, 잘못된 URL 차단 등.
- 브라우저: PC 1440, 태블릿 768, 모바일 390·320 크기, 검색 결과 없음·초기화, 지역 필터, 상세 URL 새로고침, 찜 유지·해제, 팝업 다음·Escape, 폭죽 12개를 확인했습니다.
- 별도 로컬 검증 서버로 API 모드의 목록·상세·사진 없음·오류·재시도·비로그인 찜 안내를 확인했습니다.
- 실제 팀 백엔드·로그인 서버와의 통합 검증, 실제 계정의 맞춤 추천 결과, FE2 일정 화면 연결, 배포는 남아 있습니다. 현재 백엔드 파일은 빈 상태입니다.

## 자료와 라이선스

예시 사진은 지난 행사 또는 공식 프로그램 자료입니다. 2026년 현장 사진으로 표시하지 않습니다.

- [부산불꽃축제 안내](https://www.busanfireworks.com/) / [사진 갤러리](https://www.busanfireworks.com/photo)
- [청송사과축제 안내·프로그램](https://www.csapplefestival.kr/bbs/content.php?co_id=information)
- [파주시 장단콩축제 안내·사진](https://www.paju.go.kr/tour/festival/festival02/festival02_2/festival02_2_01/festival02_2_01_01.jsp)
- 글꼴: Bagel Fat One / IBM Plex Sans KR. `public/assets/*-OFL.txt`에 SIL Open Font License 원문을 포함합니다.
- 개발 참고: [React](https://react.dev/learn/build-a-react-app-from-scratch), [Vite](https://vite.dev/guide/), [React Router](https://reactrouter.com/7.18.5/start/declarative/installation).
