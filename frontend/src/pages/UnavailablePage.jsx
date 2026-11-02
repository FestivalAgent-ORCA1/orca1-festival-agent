import { Link, useLocation } from "react-router-dom";
import EmptyState from "../components/common/EmptyState.jsx";
import Button from "../components/common/Button.jsx";
export default function UnavailablePage() {
  const { pathname } = useLocation();
  return (
    <section className="wrap unavailable-page">
      <EmptyState
        title={
          pathname === "/login"
            ? "로그인 화면을 준비하고 있어요."
            : "이 페이지를 찾을 수 없어요."
        }
      >
        <span>
          {pathname === "/login"
            ? "축제는 로그인 없이도 계속 둘러볼 수 있어요."
            : "다른 축제를 구경하러 가볼까요?"}
        </span>
        <br />
        <Button as={Link} to="/festivals" variant="blue">
          축제 구경하기
        </Button>
      </EmptyState>
    </section>
  );
}
