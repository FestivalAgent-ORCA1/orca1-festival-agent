export function createLikesApi(request) {
  return {
    async getLikes(signal) {
      const items = [];
      let page = 1;
      let total;
      do {
        const result = await request("/api/likes", {
          query: { page, size: 50 },
          signal,
        });
        if (!Array.isArray(result.items) || !Number.isFinite(result.total))
          throw new Error("찜 목록 응답을 확인해 주세요.");
        items.push(...result.items);
        total = result.total;
        if (!result.items.length) break;
        page += 1;
      } while (items.length < total);
      return [
        ...new Map(items.map((item) => [item.content_id, item])).values(),
      ];
    },
    async addLike(id) {
      try {
        await request("/api/likes", {
          method: "POST",
          body: { content_id: id },
        });
      } catch (error) {
        if (error.status !== 409 || error.code !== "ALREADY_LIKED") throw error;
      }
    },
    removeLike: (id) =>
      request(`/api/likes/${encodeURIComponent(id)}`, { method: "DELETE" }),
  };
}
