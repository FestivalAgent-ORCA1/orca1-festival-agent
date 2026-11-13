import { useCallback, useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { repository } from "../api/repository.js";
import { useAuth } from "../contexts/AuthContext.jsx";
import { useNotifications } from "../contexts/NotificationsContext.jsx";
import { useToast } from "../contexts/ToastContext.jsx";
import { useResource } from "../hooks/useResource.js";
import { parsePage } from "../lib/format.js";
import { postDate } from "../lib/postDate.js";
import Button from "../components/common/Button.jsx";
import Loading from "../components/common/Loading.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import EmptyState from "../components/common/EmptyState.jsx";

const PAGE_SIZE = 20;
// docs/db-schema.md의 notifications.type
const typeLabels = {
  FESTIVAL_D7: "D-7",
  FESTIVAL_D1: "D-1",
  FESTIVAL_START: "오늘 시작",
  SIMILAR_FESTIVAL: "비슷한 축제",
};

export default function NotificationsPage() {
  const auth = useAuth();
  if (auth.status === "loading")
    return <Loading text="로그인 정보를 확인하고 있어요." />;
  if (auth.status === "guest")
    return <Navigate to="/login?redirect=%2Fnotifications" replace />;
  return <NotificationList />;
}

function NotificationList() {
  const { unread, setUnread } = useNotifications();
  const navigate = useNavigate();
  const notify = useToast();
  const [params, setParams] = useSearchParams();
  const page = parsePage(params.get("page"));
  const load = useCallback(
    (signal) =>
      repository.getNotifications({ page, size: PAGE_SIZE }, signal),
    [page],
  );
  const result = useResource(load);
  // 읽음 처리 후에는 다시 불러오지 않고 화면의 표시만 바꿉니다.
  const [readIds, setReadIds] = useState(() => new Set());
  const [allRead, setAllRead] = useState(false);
  const items = (result.data?.items || []).map((item) =>
    allRead || readIds.has(item.id) ? { ...item, is_read: true } : item,
  );
  const lastPage = Math.max(
    1,
    Math.ceil((result.data?.total || 0) / PAGE_SIZE),
  );
  const open = async (item) => {
    if (!item.is_read) {
      try {
        await repository.markRead(item.id);
        setReadIds((previous) => new Set(previous).add(item.id));
        setUnread((count) => Math.max(0, count - 1));
      } catch {
        /* 읽음 표시가 실패해도 축제로는 이동합니다 */
      }
    }
    if (item.festival_content_id)
      navigate(`/festivals/${encodeURIComponent(item.festival_content_id)}`);
  };
  const readAll = async () => {
    try {
      await repository.markAllRead();
      setAllRead(true);
      setUnread(0);
      notify("모든 알림을 읽었어요.");
    } catch (err) {
      notify(err.message || "읽음 처리하지 못했어요.");
    }
  };
  return (
    <section className="wrap community-page">
      <div className="community-head">
        <div className="page-intro">
          <span className="eyebrow">NOTIFICATIONS</span>
          <h1 className="display">알림함</h1>
          <p>찜한 축제의 일정과 비슷한 축제 소식을 알려드려요.</p>
        </div>
        <Button
          variant="white"
          disabled={!unread || result.status !== "success"}
          onClick={readAll}
        >
          모두 읽음
        </Button>
      </div>
      {result.status === "loading" ? (
        <Loading text="알림을 불러오고 있어요." />
      ) : result.status === "error" ? (
        <ErrorState error={result.error} onRetry={result.retry} />
      ) : items.length ? (
        <>
          <ul className="notification-list">
            {items.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={`notification ${item.is_read ? "" : "unread"}`}
                  onClick={() => open(item)}
                >
                  <span className="notification-type">
                    {typeLabels[item.type] || "알림"}
                  </span>
                  <span className="notification-message">{item.message}</span>
                  <span className="notification-date">
                    {postDate(item.created_at)}
                    {!item.is_read && <span className="sr-only"> · 안 읽음</span>}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {lastPage > 1 && (
            <nav className="pagination" aria-label="알림 페이지">
              <Button
                disabled={page <= 1}
                onClick={() => setParams({ page: String(page - 1) })}
              >
                이전
              </Button>
              <span>
                {page} / {lastPage}
              </span>
              <Button
                disabled={page >= lastPage}
                onClick={() => setParams({ page: String(page + 1) })}
              >
                다음
              </Button>
            </nav>
          )}
        </>
      ) : (
        <EmptyState title="아직 도착한 알림이 없어요.">
          축제를 찜하면 시작 전에 알려드려요.
        </EmptyState>
      )}
    </section>
  );
}
