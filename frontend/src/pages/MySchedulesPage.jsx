import { useCallback, useEffect } from "react";
import { Link } from "react-router-dom";
import { repository } from "../api/repository.js";
import { useResource } from "../hooks/useResource.js";
import { visitDateLabel } from "../lib/itinerary.js";
import Button from "../components/common/Button.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import Loading from "../components/common/Loading.jsx";
import FestivalImage from "../components/festival/FestivalImage.jsx";
import "../styles/planner.css";

export default function MySchedulesPage() {
  const loggedIn = repository.hasSession();
  const resource = useResource(
    useCallback((signal) => repository.getSchedules(signal), []),
    loggedIn,
  );
  useEffect(() => {
    document.title = "내 일정 — ORCA";
    return () => {
      document.title = "ORCA — 주말의 입장권";
    };
  }, []);

  return (
    <section className="wrap schedules-page">
      <header className="page-intro schedules-head">
        <div>
          <span className="eyebrow">MY PLANS</span>
          <h1 className="display">내가 만든 하루들</h1>
        </div>
        <Button as={Link} to="/chat" variant="blue">
          AI와 새 일정 만들기
        </Button>
      </header>

      {!loggedIn && (
        <EmptyState title="로그인하면 저장한 일정을 볼 수 있어요.">
          <Button as={Link} to={`/login?redirect=${encodeURIComponent("/schedules")}`} variant="blue">
            로그인하기
          </Button>
        </EmptyState>
      )}
      {resource.status === "loading" && <Loading text="저장한 일정을 불러오고 있어요." />}
      {resource.status === "error" && <ErrorState error={resource.error} onRetry={resource.retry} />}
      {resource.status === "success" &&
        (resource.data.length ? (
          <ul className="schedule-list">
            {resource.data.map((schedule) => (
              <li key={schedule.id}>
                <Link className="schedule-card" to={`/schedules/${schedule.id}`}>
                  {schedule.festival ? (
                    <FestivalImage festival={schedule.festival} className="schedule-card-photo" loading="lazy" />
                  ) : (
                    <span className="schedule-card-photo photo-fallback" aria-hidden="true" />
                  )}
                  <span className="schedule-card-body">
                    <span className="schedule-card-date">{visitDateLabel(schedule.visit_date)}</span>
                    <strong>{schedule.title}</strong>
                    <span className="schedule-card-meta">
                      {schedule.festival?.title || "축제 정보 없음"}
                      {Number.isFinite(schedule.item_count) && ` · ${schedule.item_count}곳`}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="아직 저장한 일정이 없어요.">
            <span>AI에게 축제와 방문일을 알려 주면 하루 시간표를 만들어 드려요.</span>
            <br />
            <Button as={Link} to="/chat" variant="blue">
              일정 만들러 가기
            </Button>
          </EmptyState>
        ))}
    </section>
  );
}
