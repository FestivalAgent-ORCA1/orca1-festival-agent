import { Link, NavLink } from "react-router-dom";
import { useFavorites } from "../../contexts/FavoritesContext.jsx";
import { useAuth } from "../../contexts/AuthContext.jsx";
import Button from "../common/Button.jsx";
import Icon from "../common/Icon.jsx";
export default function Header({ onAbout }) {
  const { items, status } = useFavorites();
  const auth = useAuth();
  return (
    <header className="site-header wrap">
      <Link className="brand" to="/" aria-label="ORCA 첫 화면">
        <span className="wordmark">ORCA</span>
        <span className="brand-caption">
          전국의 축제와
          <br />
          좋아하는 하루
        </span>
      </Link>
      <nav className="main-nav" aria-label="주 메뉴">
        <NavLink
          className={({ isActive }) =>
            `key nav-explore ${isActive ? "current" : ""}`
          }
          to="/festivals"
        >
          축제 찾기
        </NavLink>
        <NavLink
          className={({ isActive }) => `key ${isActive ? "current" : ""}`}
          to="/likes"
        >
          나의 티켓{" "}
          <span
            className="nav-count"
            aria-label={`찜한 축제 ${items.length}곳`}
          >
            {status === "loading"
              ? "·"
              : status === "error"
                ? "!"
                : items.length}
          </span>
        </NavLink>
        {/* 내 정보 페이지가 생기면 로그인 상태에서는 그곳으로 연결합니다.
            작은 화면에서는 BottomNav가 이 버튼을 대신합니다. */}
        {auth.status === "authenticated" ? (
          <Button className="nav-auth" onClick={auth.logout}>
            로그아웃
          </Button>
        ) : (
          <NavLink
            className={({ isActive }) =>
              `key nav-auth ${isActive ? "current" : ""}`
            }
            to="/login"
          >
            로그인
          </NavLink>
        )}
        <Button onClick={onAbout}>
          소개 <Icon name="chevron" />
        </Button>
      </nav>
      <span className="header-meta">
        <span className="open-dot" />
        좋아하는 하루를 모으는 곳
      </span>
    </header>
  );
}
