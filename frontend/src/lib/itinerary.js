// 시간표(Itinerary) 화면과 저장에 쓰는 순수 함수 모음 (FE2)

export const categoryNames = {
  festival: "축제",
  attraction: "관광지",
  restaurant: "식당",
  cafe: "카페",
};

const pad = (value) => String(value).padStart(2, "0");

export const isTime = (value) =>
  typeof value === "string" && /^([01]\d|2[0-3]):[0-5]\d$/.test(value);

export const isDate = (value) =>
  typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);

export function toMinutes(time) {
  if (!isTime(time)) return NaN;
  const [hour, minute] = time.split(":").map(Number);
  return hour * 60 + minute;
}

export function toTime(minutes) {
  const value = Math.max(0, Math.min(23 * 60 + 59, Math.round(minutes)));
  return `${pad(Math.floor(value / 60))}:${pad(value % 60)}`;
}

export function todayInSeoul(now = new Date()) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

// "2026-11-02" → "11월 2일 (월)"
export function visitDateLabel(date) {
  if (!isDate(date)) return "날짜 미정";
  const parsed = new Date(`${date}T12:00:00+09:00`);
  if (Number.isNaN(parsed.getTime())) return "날짜 미정";
  const day = new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    weekday: "short",
  }).format(parsed);
  return `${Number(date.slice(5, 7))}월 ${Number(date.slice(8, 10))}일 (${day})`;
}

export function durationLabel(minutes) {
  if (!Number.isFinite(minutes) || minutes <= 0) return "0분";
  const hours = Math.floor(minutes / 60);
  const rest = Math.round(minutes % 60);
  if (!hours) return `${rest}분`;
  return rest ? `${hours}시간 ${rest}분` : `${hours}시간`;
}

export function distanceLabel(km) {
  if (!Number.isFinite(km)) return "";
  return km < 1 ? `${Math.round(km * 1000)}m` : `${km.toFixed(1)}km`;
}

export const sortedItems = (itinerary) =>
  [...(itinerary?.items || [])].sort((a, b) => a.seq - b.seq);

// 지도에 찍을 수 있는 좌표만 골라냅니다.
export const mapPoints = (itinerary) =>
  sortedItems(itinerary).filter(
    (item) => Number.isFinite(item.lat) && Number.isFinite(item.lng),
  );

// 저장 API(POST·PUT /api/schedules)는 Itinerary에서 warnings를 뺀 값 + title을 받습니다.
export function toSchedulePayload(itinerary, title) {
  return {
    title: String(title || "").trim(),
    festival_content_id: itinerary.festival_content_id,
    visit_date: itinerary.visit_date,
    start_time: itinerary.start_time,
    end_time: itinerary.end_time,
    total_travel_min: itinerary.total_travel_min ?? 0,
    items: sortedItems(itinerary).map((item) => ({
      seq: item.seq,
      category: item.category,
      content_id: item.content_id ?? null,
      name: item.name,
      address: item.address ?? null,
      lng: item.lng ?? null,
      lat: item.lat ?? null,
      start_time: item.start_time,
      end_time: item.end_time,
      travel_min_from_prev: item.travel_min_from_prev ?? null,
      distance_km_from_prev: item.distance_km_from_prev ?? null,
      memo: item.memo ?? null,
    })),
  };
}

// 저장된 일정 상세 응답에서 시간표 부분만 꺼냅니다.
export function itineraryOf(schedule) {
  if (!schedule) return null;
  return {
    festival_content_id: schedule.festival_content_id,
    visit_date: schedule.visit_date,
    start_time: schedule.start_time,
    end_time: schedule.end_time,
    total_travel_min: schedule.total_travel_min ?? 0,
    items: schedule.items || [],
    warnings: schedule.warnings || [],
  };
}

export function defaultScheduleTitle(itinerary, festival) {
  const name = festival?.title || "축제";
  const date = isDate(itinerary?.visit_date)
    ? ` ${Number(itinerary.visit_date.slice(5, 7))}/${Number(itinerary.visit_date.slice(8, 10))}`
    : "";
  return `${name}${date} 나들이`.slice(0, 50);
}

// 다시 계산할 때 유지할 장소 (축제 자신은 서버가 넣으므로 제외)
export const placeIdsOf = (itinerary) =>
  sortedItems(itinerary)
    .filter(
      (item) =>
        ["attraction", "restaurant", "cafe"].includes(item.category) &&
        item.content_id,
    )
    .map((item) => String(item.content_id));
