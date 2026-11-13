import { NavLink } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext.jsx";
import Icon from "../common/Icon.jsx";

// 작은 화면(620px 이하)에서만 보이는 하단 메뉴. 찜·일정·알림은 내 정보에서 들어갑니다.
export default function BottomNav() {
  const { status } = useAuth();
  const items = [
    { to: "/", label: "홈", icon: "home", end: true },
    { to: "/festivals", label: "축제", icon: "search" },
    { to: "/chat", label: "AI 일정", icon: "chat" },
    { to: "/community", label: "커뮤니티", icon: "community" },
    status === "authenticated"
      ? { to: "/profile", label: "내 정보", icon: "user" }
      : { to: "/login", label: "로그인", icon: "user" },
  ];
  return (
    <nav className="bottom-nav" aria-label="하단 메뉴">
      {items.map(({ to, label, icon, end }) => (
        <NavLink key={to} to={to} end={end} className="bottom-nav-item">
          <Icon name={icon} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
