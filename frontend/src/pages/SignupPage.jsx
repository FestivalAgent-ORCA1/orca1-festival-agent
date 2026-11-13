import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { safeRedirect, useAuth } from "../contexts/AuthContext.jsx";
import Button from "../components/common/Button.jsx";
import Loading from "../components/common/Loading.jsx";

export default function SignupPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const redirect = safeRedirect(params.get("redirect"));
  const [form, setForm] = useState({ email: "", password: "", nickname: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  if (auth.status === "loading")
    return <Loading text="로그인 정보를 확인하고 있어요." />;
  if (auth.status === "authenticated" && !submitting)
    return <Navigate to={redirect} replace />;
  const change = (key) => (event) =>
    setForm((previous) => ({ ...previous, [key]: event.target.value }));
  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await auth.signup(form.email, form.password, form.nickname.trim());
      navigate(`/onboarding?redirect=${encodeURIComponent(redirect)}`, {
        replace: true,
      });
    } catch (err) {
      setError(err.message || "가입하지 못했어요. 다시 시도해 주세요.");
      setSubmitting(false);
    }
  };
  return (
    <section className="wrap auth-page">
      <div className="auth-card">
        <div className="page-intro">
          <span className="eyebrow">JOIN THE WEEKEND CLUB</span>
          <h1 className="display">주말의 입장권, 한 장 받기.</h1>
          <p>가입하면 찜한 축제를 모으고 나에게 맞는 추천을 받을 수 있어요.</p>
        </div>
        <form className="auth-form" onSubmit={submit}>
          <label className="auth-field">
            이메일
            <input
              type="email"
              autoComplete="email"
              required
              value={form.email}
              onChange={change("email")}
            />
          </label>
          <label className="auth-field">
            <span>
              비밀번호 <span className="auth-hint">8자 이상</span>
            </span>
            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={form.password}
              onChange={change("password")}
            />
          </label>
          <label className="auth-field">
            <span>
              닉네임 <span className="auth-hint">2~15자</span>
            </span>
            <input
              type="text"
              autoComplete="nickname"
              required
              minLength={2}
              maxLength={15}
              value={form.nickname}
              onChange={change("nickname")}
            />
          </label>
          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}
          <Button variant="blue" type="submit" disabled={submitting}>
            {submitting ? "가입하는 중…" : "가입하기"}
          </Button>
        </form>
        <p className="auth-switch">
          이미 계정이 있나요?{" "}
          <Link to={`/login?redirect=${encodeURIComponent(redirect)}`}>
            로그인
          </Link>
        </p>
      </div>
    </section>
  );
}
