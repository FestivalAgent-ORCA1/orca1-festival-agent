import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { safeRedirect, useAuth } from "../contexts/AuthContext.jsx";
import { repository } from "../api/repository.js";
import Button from "../components/common/Button.jsx";
import Loading from "../components/common/Loading.jsx";

export default function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const redirect = safeRedirect(params.get("redirect"));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  if (auth.status === "loading")
    return <Loading text="로그인 정보를 확인하고 있어요." />;
  if (auth.status === "authenticated" && !submitting)
    return <Navigate to={redirect} replace />;
  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const user = await auth.login(email, password);
      navigate(
        user.onboarded
          ? redirect
          : `/onboarding?redirect=${encodeURIComponent(redirect)}`,
        { replace: true },
      );
    } catch (err) {
      setError(err.message || "로그인하지 못했어요. 다시 시도해 주세요.");
      setSubmitting(false);
    }
  };
  return (
    <section className="wrap auth-page">
      <div className="auth-card">
        <div className="page-intro">
          <span className="eyebrow">WELCOME BACK</span>
          <h1 className="display">다시 만나서 반가워요.</h1>
          <p>
            {repository.mode === "mock"
              ? "미리 보기에서는 이 브라우저에서 가입한 이메일과 8자 이상의 비밀번호로 로그인돼요."
              : "로그인하면 찜한 축제와 맞춤 추천을 볼 수 있어요."}
          </p>
        </div>
        <form className="auth-form" onSubmit={submit}>
          <label className="auth-field">
            이메일
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="auth-field">
            비밀번호
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}
          <Button variant="blue" type="submit" disabled={submitting}>
            {submitting ? "로그인하는 중…" : "로그인"}
          </Button>
        </form>
        <p className="auth-switch">
          아직 계정이 없나요?{" "}
          <Link to={`/signup?redirect=${encodeURIComponent(redirect)}`}>
            가입하기
          </Link>
        </p>
      </div>
    </section>
  );
}
