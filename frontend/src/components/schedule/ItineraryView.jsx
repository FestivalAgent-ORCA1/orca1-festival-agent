import { useState } from "react";
import { durationLabel, mapPoints, sortedItems, visitDateLabel } from "../../lib/itinerary.js";
import Timeline from "./Timeline.jsx";
import KakaoMap from "./KakaoMap.jsx";
import "../../styles/planner.css";

// 시간표 + 지도 묶음. 채팅의 timeline 블록과 일정 상세 페이지에서 함께 씁니다.
export default function ItineraryView({ itinerary, layout = "stack", actions = null }) {
  const [activeSeq, setActiveSeq] = useState(null);
  const select = (seq) => setActiveSeq((current) => (current === seq ? null : seq));
  const items = sortedItems(itinerary);
  const warnings = Array.isArray(itinerary?.warnings) ? itinerary.warnings : [];
  return (
    <div className={`itinerary itinerary--${layout}`}>
      <div className="itinerary-summary">
        <strong>{visitDateLabel(itinerary.visit_date)}</strong>
        <span>
          {itinerary.start_time} ~ {itinerary.end_time}
        </span>
        <span>{items.length}곳</span>
        <span>이동 {durationLabel(itinerary.total_travel_min)}</span>
      </div>
      {warnings.length > 0 && (
        <ul className="itinerary-warnings" aria-label="일정 안내">
          {warnings.map((warning, index) => (
            <li key={`${warning.code}-${index}`}>{warning.message}</li>
          ))}
        </ul>
      )}
      <div className="itinerary-body">
        <KakaoMap points={mapPoints(itinerary)} activeSeq={activeSeq} onSelect={select} />
        <Timeline itinerary={itinerary} activeSeq={activeSeq} onSelect={select} />
      </div>
      {actions && <div className="itinerary-actions">{actions}</div>}
    </div>
  );
}
