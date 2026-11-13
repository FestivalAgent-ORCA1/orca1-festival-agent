import { useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { safeRedirect, useAuth } from "../contexts/AuthContext.jsx";
import { regions, tagNames } from "../data/festivals.js";
import { ageGroups } from "../data/preferences.js";
import Button from "../components/common/Button.jsx";
import Loading from "../components/common/Loading.jsx";
import ErrorState from "../components/common/ErrorState.jsx";

const MAX_REGIONS = 3;
const MAX_TAGS = 5;

function toggle(list, value, max) {
  if (list.includes(value)) return list.filter((item) => item !== value);
  return list.length < max ? [...list, value] : list;
}

export default function OnboardingPage() {
  const auth = useAuth();
  if (auth.status === "loading")
    return <Loading text="내 정보를 불러오고 있어요." />;
  if (auth.status === "error")
    return (
      <section className="wrap auth-page">
        <ErrorState error={auth.error} onRetry={auth.retry} />
      </section>
    );
  if (auth.status === "guest")
    return <Navigate to="/login?redirect=%2Fonboarding" replace />;
  // user가 준비된 뒤에 그려야 기존 선택값으로 시작할 수 있습니다.
  return <PreferencesForm key={auth.user.id} />;
}

function PreferencesForm() {
  const { user, updatePreferences } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const redirect = safeRedirect(params.get("redirect"));
  const [ageGroup, setAgeGroup] = useState(user.age_group || "");
  const [picked, setPicked] = useState({
    regions: user.regions || [],
    tags: user.tags || [],
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const pick = (key, value, max) =>
    setPicked((previous) => ({
      ...previous,
      [key]: toggle(previous[key], value, max),
    }));
  const submit = async (event) => {
    event.preventDefault();
    if (!picked.tags.length) {
      setError("관심사를 하나 이상 골라 주세요.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await updatePreferences({ age_group: ageGroup || null, ...picked });
      navigate(redirect, { replace: true });
    } catch (err) {
      setError(err.message || "저장하지 못했어요. 다시 시도해 주세요.");
      setSubmitting(false);
    }
  };
  return (
    <section className="wrap auth-page">
      <div className="auth-card wide">
        <div className="page-intro">
          <span className="eyebrow">FIRST SETTINGS</span>
          <h1 className="display">{user.nickname}님의 주말 취향.</h1>
          <p>
            고른 내용으로 축제를 추천해 드려요. 내 정보에서 언제든 바꿀 수
            있어요.
          </p>
        </div>
        <form className="auth-form" onSubmit={submit}>
          <label className="auth-field">
            <span>
              연령대 <span className="auth-hint">선택</span>
            </span>
            <select
              value={ageGroup}
              onChange={(event) => setAgeGroup(event.target.value)}
            >
              <option value="">선택하지 않을게요</option>
              {ageGroups.map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <fieldset className="choice-group">
            <legend>
              자주 가고 싶은 지역{" "}
              <span className="auth-hint">
                {picked.regions.length}/{MAX_REGIONS} · 고르지 않으면 전국
              </span>
            </legend>
            <div className="filters">
              {regions.map(([code, name]) => (
                <button
                  key={code}
                  className="mood"
                  type="button"
                  aria-pressed={picked.regions.includes(code)}
                  onClick={() => pick("regions", code, MAX_REGIONS)}
                >
                  {name}
                </button>
              ))}
            </div>
          </fieldset>
          <fieldset className="choice-group">
            <legend>
              관심사{" "}
              <span className="auth-hint">
                {picked.tags.length}/{MAX_TAGS} · 1개 이상
              </span>
            </legend>
            <div className="filters">
              {Object.entries(tagNames).map(([code, name]) => (
                <button
                  key={code}
                  className="mood"
                  type="button"
                  aria-pressed={picked.tags.includes(code)}
                  onClick={() => pick("tags", code, MAX_TAGS)}
                >
                  {name}
                </button>
              ))}
            </div>
          </fieldset>
          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}
          <Button variant="blue" type="submit" disabled={submitting}>
            {submitting ? "저장하는 중…" : "이대로 시작하기"}
          </Button>
        </form>
      </div>
    </section>
  );
}
