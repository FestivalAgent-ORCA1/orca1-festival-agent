import { categoryNames, distanceLabel } from "../../lib/itinerary.js";

export default function TimelineItem({ item, active = false, onSelect }) {
  const travel = item.travel_min_from_prev;
  const distance = distanceLabel(item.distance_km_from_prev);
  return (
    <li className={`timeline-item ${active ? "is-active" : ""}`}>
      {Number.isFinite(travel) && (
        <p className="timeline-leg">
          <span aria-hidden="true">↓</span> 차로 약 {travel}분{distance && ` · ${distance}`}
        </p>
      )}
      <button
        type="button"
        className={`timeline-stop timeline-stop--${item.category}`}
        aria-pressed={active}
        onClick={() => onSelect?.(item.seq)}
      >
        <span className="timeline-seq" aria-hidden="true">
          {item.seq}
        </span>
        <span className="timeline-time">
          <strong>{item.start_time}</strong>
          <span>~ {item.end_time}</span>
        </span>
        <span className="timeline-body">
          <span className="timeline-category">
            {categoryNames[item.category] || "장소"}
          </span>
          <strong className="timeline-name">{item.name}</strong>
          {item.address && <span className="timeline-address">{item.address}</span>}
          {item.memo && <span className="timeline-memo">{item.memo}</span>}
        </span>
      </button>
    </li>
  );
}
