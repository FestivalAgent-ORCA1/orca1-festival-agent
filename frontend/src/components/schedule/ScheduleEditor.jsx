import { useState } from "react";
import { repository } from "../../api/repository.js";
import { categoryNames, placeIdsOf, sortedItems, toMinutes } from "../../lib/itinerary.js";
import Button from "../common/Button.jsx";
import PlacePicker from "./PlacePicker.jsx";

// 저장된 일정의 조건(이름·날짜·시간·장소)을 바꿔서 POST /api/itinerary/calculate로 다시 계산합니다.
// 계산 결과는 onCalculated(itinerary, title)로 부모에게 넘기고, 저장은 부모가 합니다.
export default function ScheduleEditor({ schedule, onCalculated, onCancel }) {
  const festival = schedule.festival;
  const [title, setTitle] = useState(schedule.title || "");
  const [visitDate, setVisitDate] = useState(schedule.visit_date);
  const [startTime, setStartTime] = useState(schedule.start_time);
  const [endTime, setEndTime] = useState(schedule.end_time);
  const [autoFill, setAutoFill] = useState(true);
  const [places, setPlaces] = useState(() =>
    sortedItems(schedule)
      .filter((item) => placeIdsOf({ items: [item] }).length)
      .map((item) => ({ content_id: String(item.content_id), name: item.name, category: item.category })),
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    if (!title.trim()) return setError("일정 이름을 적어 주세요.");
    if (!(toMinutes(endTime) > toMinutes(startTime)))
      return setError("끝나는 시각은 시작 시각보다 늦어야 해요.");
    setBusy(true);
    setError("");
    try {
      const itinerary = await repository.calculateItinerary({
        festival_content_id: schedule.festival_content_id,
        visit_date: visitDate,
        start_time: startTime,
        end_time: endTime,
        place_ids: places.map((place) => place.content_id),
        auto_fill: autoFill,
      });
      onCalculated(itinerary, title.trim());
    } catch (failure) {
      setError(failure?.message || "시간표를 다시 계산하지 못했어요.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="schedule-editor" onSubmit={submit}>
      <h2 className="schedule-editor-title">조건을 바꿔 다시 계산하기</h2>
      <div className="schedule-editor-grid">
        <label className="field field--wide">
          <span>일정 이름</span>
          <input value={title} maxLength={50} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label className="field">
          <span>방문일</span>
          <input
            type="date"
            value={visitDate}
            min={festival?.start_date}
            max={festival?.end_date}
            onChange={(e) => setVisitDate(e.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>시작</span>
          <input type="time" value={startTime} step="600" onChange={(e) => setStartTime(e.target.value)} required />
        </label>
        <label className="field">
          <span>끝</span>
          <input type="time" value={endTime} step="600" onChange={(e) => setEndTime(e.target.value)} required />
        </label>
      </div>
      {festival && (
        <p className="field-hint">
          축제 기간: {festival.start_date} ~ {festival.end_date}
        </p>
      )}

      <div className="picked-places">
        <strong>꼭 넣을 장소 {places.length ? `${places.length}곳` : ""}</strong>
        {places.length ? (
          <ul>
            {places.map((place) => (
              <li key={place.content_id}>
                <span>
                  {categoryNames[place.category] || "장소"} · {place.name}
                </span>
                <button
                  type="button"
                  aria-label={`${place.name} 빼기`}
                  onClick={() => setPlaces((list) => list.filter((p) => p.content_id !== place.content_id))}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="field-hint">아래에서 장소를 담거나, 자동 채우기를 켜 두세요.</p>
        )}
        <label className="check">
          <input type="checkbox" checked={autoFill} onChange={(e) => setAutoFill(e.target.checked)} />
          부족한 식사·관광지는 자동으로 채우기
        </label>
      </div>

      <PlacePicker
        festivalContentId={schedule.festival_content_id}
        selectedIds={places.map((place) => place.content_id)}
        onAdd={(place) =>
          setPlaces((list) => [
            ...list,
            { content_id: String(place.content_id), name: place.name, category: place.category },
          ])
        }
        onRemove={(id) => setPlaces((list) => list.filter((p) => p.content_id !== String(id)))}
      />

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <div className="planner-form-actions">
        <Button variant="white" onClick={onCancel} disabled={busy}>
          닫기
        </Button>
        <Button type="submit" variant="blue" disabled={busy}>
          {busy ? "계산하는 중… (몇 초 걸려요)" : "다시 계산하기"}
        </Button>
      </div>
    </form>
  );
}
