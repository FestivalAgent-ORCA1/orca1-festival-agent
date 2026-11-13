const formatter = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

// 글·댓글·알림의 작성일을 "2026. 11. 13." 모양으로 보여줍니다.
export function postDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : formatter.format(date);
}
