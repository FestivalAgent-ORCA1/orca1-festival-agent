import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { repository } from "../api/repository.js";
import { useResource } from "../hooks/useResource.js";
import { useAuth } from "../contexts/AuthContext.jsx";
import { useToast } from "../contexts/ToastContext.jsx";
import { itineraryOf, toSchedulePayload } from "../lib/itinerary.js";
import Button from "../components/common/Button.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import Loading from "../components/common/Loading.jsx";
import Modal from "../components/common/Modal.jsx";
import ItineraryView from "../components/schedule/ItineraryView.jsx";
import ScheduleEditor from "../components/schedule/ScheduleEditor.jsx";
import "../styles/planner.css";

export default function ScheduleDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const notify = useToast();
  const loggedIn = useAuth().status !== "guest";
  const resource = useResource(
    useCallback((signal) => repository.getSchedule(id, signal), [id]),
    loggedIn,
  );
  const [schedule, setSchedule] = useState(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(null); // { itinerary, title } 다시 계산했지만 아직 저장 안 함
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (resource.status === "success") setSchedule(resource.data);
  }, [resource.status, resource.data]);
  useEffect(() => {
    if (schedule?.title) document.title = `${schedule.title} — ORCA`;
    return () => {
      document.title = "ORCA — 주말의 입장권";
    };
  }, [schedule?.title]);

  const saveDraft = async () => {
    setBusy(true);
    try {
      const updated = await repository.updateSchedule(id, toSchedulePayload(draft.itinerary, draft.title));
      setSchedule({ ...schedule, ...itineraryOf(draft.itinerary), title: draft.title, ...(updated || {}) });
      setDraft(null);
      setEditing(false);
      notify("새 시간표로 저장했어요.");
    } catch (error) {
      notify(error?.message || "일정을 저장하지 못했어요.");
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    try {
      await repository.deleteSchedule(id);
      notify("일정을 삭제했어요.");
      navigate("/schedules", { replace: true });
    } catch (error) {
      notify(error?.message || "일정을 삭제하지 못했어요.");
      setBusy(false);
      setConfirmDelete(false);
    }
  };

  const shown = draft ? draft.itinerary : itineraryOf(schedule);

  return (
    <section className="wrap schedule-detail-page">
      <Link className="back-link" to="/schedules">
        ← 내 일정으로
      </Link>

      {!loggedIn && (
        <EmptyState title="로그인하면 저장한 일정을 볼 수 있어요.">
          <Button as={Link} to={`/login?redirect=${encodeURIComponent(`/schedules/${id}`)}`} variant="blue">
            로그인하기
          </Button>
        </EmptyState>
      )}
      {resource.status === "loading" && <Loading text="일정을 펼치고 있어요." />}
      {resource.status === "error" &&
        (resource.error.status === 404 ? (
          <EmptyState title="이 일정을 찾을 수 없어요.">
            <Button as={Link} to="/schedules" variant="white">
              내 일정 목록으로
            </Button>
          </EmptyState>
        ) : (
          <ErrorState error={resource.error} onRetry={resource.retry} />
        ))}

      {schedule && (
        <>
          <header className="schedule-detail-head">
            <div>
              <span className="eyebrow">MY PLAN</span>
              <h1 className="planner-title">{draft ? draft.title : schedule.title}</h1>
              {schedule.festival && (
                <Link className="schedule-festival-link" to={`/festivals/${encodeURIComponent(schedule.festival.content_id)}`}>
                  {schedule.festival.title} 보러 가기 →
                </Link>
              )}
            </div>
            {!editing && (
              <div className="schedule-detail-actions">
                <Button variant="white" onClick={() => setEditing(true)}>
                  다시 계산하기
                </Button>
                <Button onClick={() => setConfirmDelete(true)}>삭제</Button>
              </div>
            )}
          </header>

          {editing && (
            <ScheduleEditor
              schedule={schedule}
              onCalculated={(itinerary, title) => setDraft({ itinerary, title })}
              onCancel={() => {
                setEditing(false);
                setDraft(null);
              }}
            />
          )}

          {draft && (
            <div className="draft-banner" role="status">
              <p>새로 계산한 시간표예요. 아직 저장하지 않았어요.</p>
              <div>
                <Button variant="white" onClick={() => setDraft(null)} disabled={busy}>
                  원래대로
                </Button>
                <Button variant="blue" onClick={saveDraft} disabled={busy}>
                  {busy ? "저장하는 중…" : "이 시간표로 저장"}
                </Button>
              </div>
            </div>
          )}

          <ItineraryView key={draft ? "draft" : "saved"} itinerary={shown} layout="split" />
        </>
      )}

      <Modal open={confirmDelete} title="일정 삭제" onClose={() => !busy && setConfirmDelete(false)} className="planner-dialog">
        <div className="planner-form">
          <h2 className="planner-title">이 일정을 삭제할까요?</h2>
          <p>삭제한 일정은 되돌릴 수 없어요.</p>
          <div className="planner-form-actions">
            <Button variant="white" onClick={() => setConfirmDelete(false)} disabled={busy}>
              취소
            </Button>
            <Button variant="blue" onClick={remove} disabled={busy}>
              {busy ? "삭제하는 중…" : "삭제하기"}
            </Button>
          </div>
        </div>
      </Modal>
    </section>
  );
}
