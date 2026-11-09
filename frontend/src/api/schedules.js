// 일정 저장 API (api-spec.md 9장). 모두 로그인 필요.
export function createSchedulesApi(request) {
  return {
    async getSchedules(signal) {
      const items = [];
      let page = 1;
      let total = Infinity;
      while (items.length < total) {
        const result = await request("/api/schedules", {
          query: { page, size: 50 },
          signal,
        });
        // 목록 형식({ items, total })과 배열 응답을 모두 받습니다.
        if (Array.isArray(result)) return result;
        if (!Array.isArray(result?.items))
          throw new Error("일정 목록 응답을 확인해 주세요.");
        items.push(...result.items);
        total = Number.isFinite(result.total) ? result.total : items.length;
        if (!result.items.length) break;
        page += 1;
      }
      return items;
    },
    getSchedule: (id, signal) =>
      request(`/api/schedules/${encodeURIComponent(id)}`, { signal }),
    createSchedule: (payload) =>
      request("/api/schedules", { method: "POST", body: payload }),
    updateSchedule: (id, payload) =>
      request(`/api/schedules/${encodeURIComponent(id)}`, {
        method: "PUT",
        body: payload,
      }),
    deleteSchedule: (id) =>
      request(`/api/schedules/${encodeURIComponent(id)}`, {
        method: "DELETE",
        allowEmptyResponse: true,
      }),
  };
}
