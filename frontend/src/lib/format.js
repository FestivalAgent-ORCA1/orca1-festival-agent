export const safeExternalUrl = (value) => {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
};
export const safeImageUrl = (value) =>
  typeof value === "string" && value.startsWith("/assets/")
    ? value
    : safeExternalUrl(value);
export const plainText = (value) =>
  String(value || "")
    .replace(/<br\s*\/?\s*>/gi, "\n")
    .replace(/<[^>]*>/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .trim();
export function dateLabel(start, end, { year = false } = {}) {
  const format = (date) =>
    /^\d{4}-\d{2}-\d{2}$/.test(date || "")
      ? `${year ? `${date.slice(0, 4)}. ` : ""}${date.slice(5, 7)}.${date.slice(8, 10)}`
      : "일정 확인 중";
  return start === end || !end
    ? format(start)
    : `${format(start)} — ${format(end)}`;
}
export function festivalStatus(
  festival,
  today = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date()),
) {
  if (festival.status) return festival.status;
  return festival.end_date < today
    ? "ended"
    : festival.start_date > today
      ? "upcoming"
      : "ongoing";
}
export const statusNames = {
  upcoming: "개최 예정",
  ongoing: "지금 열리는 중",
  ended: "종료된 축제",
};
export const parsePage = (value) =>
  Number.isFinite(Number(value)) ? Math.max(1, Math.floor(Number(value))) : 1;
