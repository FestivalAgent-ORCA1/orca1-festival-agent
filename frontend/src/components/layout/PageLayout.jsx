import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { repository } from "../../api/repository.js";
import Header from "./Header.jsx";
import BottomNav from "./BottomNav.jsx";
import Modal from "../common/Modal.jsx";
export default function PageLayout() {
  const [dialog, setDialog] = useState(null);
  const { pathname } = useLocation();
  useEffect(() => {
    setDialog(null);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname]);
  return (
    <>
      <a className="skip" href="#main-content">
        본문으로 바로 가기
      </a>
      {repository.mode === "mock" && (
        <div className="demo-notice">
          미리 보기 · 예시 축제 3곳을 담았어요. 찜은 이 브라우저에 저장돼요.
        </div>
      )}
      <Header onAbout={() => setDialog("about")} />
      <main id="main-content" tabIndex="-1">
        <Outlet />
      </main>
      <footer className="footer">
        <div className="footer-inner wrap">
          <Link to="/" className="wordmark" aria-label="ORCA 첫 화면">
            ORCA
          </Link>
          <div className="footer-note">
            <span>좋아하는 하루를 찾는 작은 출발점.</span>
            <button type="button" onClick={() => setDialog("credits")}>
              행사 정보와 사진 출처
            </button>
          </div>
          <span className="copyright">© {new Date().getFullYear()} ORCA</span>
        </div>
      </footer>
      <BottomNav />
      <Modal
        open={dialog === "about"}
        title="ORCA 소개"
        onClose={() => setDialog(null)}
      >
        <div className="about-body">
          <span className="eyebrow">ORCA / WEEKEND CLUB</span>
          <h2 className="display">주말의 즐거움, 한 장.</h2>
          <p>
            ORCA는 전국의 축제를 둘러보고, 마음에 드는 곳을 모아 나만의 하루를
            계획하는 공간이에요.
          </p>
          <p>
            어디로 갈지 몰랐던 주말에 작은 출발점이 되었으면 해요. 사진 한 장에
            끌려 들어왔다가, 좋아하는 축제 하나를 발견하는 것부터 시작해봐요.
          </p>
          {repository.mode === "mock" && (
            <p className="about-foot">
              지금은 예시 축제로 둘러보는 미리 보기예요. 찜은 현재 브라우저에만
              저장되며, 예매나 결제가 이루어지지 않아요.
            </p>
          )}
        </div>
      </Modal>
      <Modal
        open={dialog === "credits"}
        title="행사 정보와 사진 출처"
        onClose={() => setDialog(null)}
      >
        <div className="about-body">
          <span className="eyebrow">CREDITS & SOURCES</span>
          <h2>행사 정보와 사진 출처</h2>
          {repository.mode === "mock" ? (
            <>
              <p>
                예시 축제의 일정과 장소는 공식 안내를 기준으로 구성했어요.
                사진은 지난 행사 또는 공식 프로그램 자료이며, 올해 현장 사진을
                뜻하지 않아요.
              </p>
              <ul>
                <li>
                  <a
                    href="https://www.busanfireworks.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    부산불꽃축제 공식 안내
                  </a>{" "}
                  ·{" "}
                  <a
                    href="https://www.busanfireworks.com/photo"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    공식 사진 갤러리
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.csapplefestival.kr/bbs/content.php?co_id=information"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    청송사과축제 공식 안내·프로그램 사진
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.paju.go.kr/tour/festival/festival02/festival02_2/festival02_2_01/festival02_2_01_01.jsp"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    파주시 장단콩축제 공식 안내·사진
                  </a>
                </li>
              </ul>
            </>
          ) : (
            <p>
              축제 정보와 사진은 한국관광공사 TourAPI를 통해 제공돼요. 일정과
              운영 정보는 방문 전 주최 측 공식 안내를 확인해 주세요.
            </p>
          )}
          <p>글꼴: Bagel Fat One / IBM Plex Sans KR, SIL Open Font License.</p>
        </div>
      </Modal>
    </>
  );
}
