import { sortedItems } from "../../lib/itinerary.js";
import TimelineItem from "./TimelineItem.jsx";

export default function Timeline({ itinerary, activeSeq = null, onSelect }) {
  const items = sortedItems(itinerary);
  if (!items.length)
    return <p className="timeline-empty">시간표에 담긴 장소가 없어요.</p>;
  return (
    <ol className="timeline" aria-label="방문 순서와 시간">
      {items.map((item) => (
        <TimelineItem
          key={`${item.seq}-${item.content_id ?? item.name}`}
          item={item}
          active={item.seq === activeSeq}
          onSelect={onSelect}
        />
      ))}
    </ol>
  );
}
