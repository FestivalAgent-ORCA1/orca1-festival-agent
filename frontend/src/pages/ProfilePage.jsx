import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext.jsx";
import { useToast } from "../contexts/ToastContext.jsx";
import { regions, tagNames } from "../data/festivals.js";
import { ageGroups } from "../data/preferences.js";
import { postDate } from "../lib/postDate.js";
import Button from "../components/common/Button.jsx";
import TagChip from "../components/common/TagChip.jsx";
import Loading from "../components/common/Loading.jsx";
import ErrorState from "../components/common/ErrorState.jsx";

const regionName = Object.fromEntries(regions);
const ageName = Object.fromEntries(ageGroups);

export default function ProfilePage() {
  const auth = useAuth();
  if (auth.status === "loading")
    return <Loading text="내 정보를 불러오고 있어요." />;
  if (auth.status === "error")
    return (
      <section className="wrap profile-page">
        <ErrorState error={auth.error} onRetry={auth.retry} />
      </section>
    );
  if (auth.status === "guest")
    return <Navigate to="/login?redirect=%2Fprofile" replace />;
  return <Profile key={auth.user.id} />;
}

function Profile() {
  const { user, updateNickname, logout, withdraw } = useAuth();
  const navigate = useNavigate();
  const notify = useToast();
  return (
    <section className="wrap profile-page">
      <div className="page-intro">
        <span className="eyebrow">MY WEEKEND CLUB</span>
        <h1 className="display">{user.nickname}님, 반가워요.</h1>
        <p>
          {user.email} · {postDate(user.created_at)} 가입
        </p>
      </div>
      <div className="profile-grid">
        <section className="profile-card">
          <h2>바로 가기</h2>
          <nav className="profile-links" aria-label="내 정보 바로 가기">
            <Link to="/likes">나의 티켓 (찜한 축제)</Link>
            <Link to="/schedules">내 일정</Link>
            <Link to="/notifications">알림함</Link>
            <Link to="/community">커뮤니티</Link>
          </nav>
        </section>
        <NicknameCard
          nickname={user.nickname}
          onSave={async (nickname) => {
            await updateNickname(nickname);
            notify("닉네임을 바꿨어요.");
          }}
        />
        <section className="profile-card">
          <div className="profile-card-head">
            <h2>내 주말 취향</h2>
            <Button
              as={Link}
              variant="white"
              to="/onboarding?redirect=%2Fprofile"
            >
              바꾸기
            </Button>
          </div>
          <dl className="profile-prefs">
            <dt>연령대</dt>
            <dd>{ageName[user.age_group] || "선택하지 않음"}</dd>
            <dt>지역</dt>
            <dd>
              {user.regions?.length
                ? user.regions.map((code) => (
                    <TagChip key={code}>{regionName[code] || code}</TagChip>
                  ))
                : "전국"}
            </dd>
            <dt>관심사</dt>
            <dd>
              {user.tags?.length
                ? user.tags.map((code) => (
                    <TagChip key={code}>{tagNames[code] || code}</TagChip>
                  ))
                : "아직 고르지 않았어요"}
            </dd>
          </dl>
        </section>
        <AccountCard
          // 화면을 먼저 옮기고 로그아웃해야 로그인 화면으로 튕기지 않습니다.
          onLogout={() => {
            navigate("/", { replace: true });
            logout();
            notify("로그아웃했어요.");
          }}
          onWithdraw={async () => {
            await withdraw();
            navigate("/", { replace: true });
            logout();
            notify("탈퇴했어요. 그동안 함께해 주셔서 고마워요.");
          }}
        />
      </div>
    </section>
  );
}

function NicknameCard({ nickname, onSave }) {
  const [value, setValue] = useState(nickname);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault();
    const next = value.trim();
    if (next.length < 2 || next.length > 15) {
      setError("닉네임은 2~15자로 입력해 주세요.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await onSave(next);
    } catch (err) {
      setError(err.message || "닉네임을 바꾸지 못했어요.");
    } finally {
      setSaving(false);
    }
  };
  return (
    <section className="profile-card">
      <h2>닉네임</h2>
      <form className="profile-inline" onSubmit={submit}>
        <label className="sr-only" htmlFor="profile-nickname">
          닉네임
        </label>
        <input
          id="profile-nickname"
          type="text"
          required
          minLength={2}
          maxLength={15}
          value={value}
          onChange={(event) => setValue(event.target.value)}
        />
        <Button
          variant="blue"
          type="submit"
          disabled={saving || value.trim() === nickname}
        >
          {saving ? "저장 중…" : "저장"}
        </Button>
      </form>
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}

function AccountCard({ onLogout, onWithdraw }) {
  const [confirming, setConfirming] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const withdraw = async () => {
    setWorking(true);
    setError("");
    try {
      await onWithdraw();
    } catch (err) {
      setError(err.message || "탈퇴하지 못했어요. 다시 시도해 주세요.");
      setWorking(false);
    }
  };
  return (
    <section className="profile-card">
      <h2>계정</h2>
      <div className="post-actions">
        <Button variant="white" onClick={onLogout}>
          로그아웃
        </Button>
        {!confirming && (
          <button
            type="button"
            className="text-button"
            onClick={() => setConfirming(true)}
          >
            회원 탈퇴
          </button>
        )}
      </div>
      {confirming && (
        <div className="post-actions" role="group" aria-label="탈퇴 확인">
          <span>탈퇴하면 찜·일정·글이 모두 사라지고 되돌릴 수 없어요.</span>
          <Button className="danger" disabled={working} onClick={withdraw}>
            {working ? "처리 중…" : "탈퇴하기"}
          </Button>
          <Button variant="white" onClick={() => setConfirming(false)}>
            취소
          </Button>
        </div>
      )}
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
