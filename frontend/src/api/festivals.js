export function createFestivalApi(request) {
  return {
    getFestivals: (query, signal) =>
      request("/api/festivals", { query, signal }),
    getDetail: (id, signal) =>
      request(`/api/festivals/${encodeURIComponent(id)}`, { signal }),
    getSimilar: (id, signal) =>
      request(`/api/festivals/${encodeURIComponent(id)}/similar`, { signal }),
    getRecommended: (signal) =>
      request("/api/festivals/recommended", { query: { size: 3 }, signal }),
  };
}
