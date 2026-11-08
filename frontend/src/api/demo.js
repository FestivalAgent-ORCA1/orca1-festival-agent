import { ApiError } from "./client.js";
import { demoFestivals } from "../data/festivals.js";
import { festivalStatus, parsePage } from "../lib/format.js";

export function filterFestivals(items, query = {}) {
  const keyword = (query.keyword || "").replace(/\s/g, "").toLocaleLowerCase();
  const codes = String(query.area_code || "")
    .split(",")
    .filter(Boolean);
  const tags = String(query.tags || "")
    .split(",")
    .filter(Boolean);
  let found = items.filter(
    (item) =>
      (!keyword ||
        `${item.title}${item.address}`
          .replace(/\s/g, "")
          .toLocaleLowerCase()
          .includes(keyword)) &&
      (!codes.length || codes.includes(item.area_code)) &&
      (!tags.length || tags.some((tag) => item.tags.includes(tag))) &&
      (!query.status || festivalStatus(item) === query.status) &&
      (!query.start_date || item.end_date >= query.start_date) &&
      (!query.end_date || item.start_date <= query.end_date),
  );
  const sort = ["start_date", "end_date", "title"].includes(query.sort)
    ? query.sort
    : "start_date";
  found = found.toSorted((a, b) => a[sort].localeCompare(b[sort], "ko"));
  const page = parsePage(query.page),
    size = Math.min(50, parsePage(query.size || 20));
  return {
    items: found.slice((page - 1) * size, page * size),
    page,
    size,
    total: found.length,
  };
}

export function createDemoRepository(storage) {
  const key = "orca:demo:likes:v1";
  let ids = new Set();
  let storageWarning = false;
  try {
    const stored = JSON.parse(storage?.getItem(key) || "[]");
    if (Array.isArray(stored))
      ids = new Set(
        stored.filter((id) =>
          demoFestivals.some((item) => item.content_id === id),
        ),
      );
  } catch {
    storageWarning = true;
  }
  const persist = () => {
    try {
      if (!storage) throw new Error();
      storage.setItem(key, JSON.stringify([...ids]));
    } catch {
      storageWarning = true;
    }
  };
  const decorate = (item) => ({
    ...item,
    status: festivalStatus(item),
    is_liked: ids.has(item.content_id),
  });
  return {
    mode: "mock",
    hasSession: () => true,
    get storageWarning() {
      return storageWarning;
    },
    getFestivals: async (query) =>
      filterFestivals(demoFestivals.map(decorate), query),
    getDetail: async (id) => {
      const item = demoFestivals.find((item) => item.content_id === id);
      if (!item)
        throw new ApiError(404, "FESTIVAL_NOT_FOUND", "축제를 찾을 수 없어요.");
      return decorate(item);
    },
    getSimilar: async (id) =>
      demoFestivals.filter((item) => item.content_id !== id).map(decorate),
    getRecommended: async () => [],
    getLikes: async () =>
      demoFestivals.filter((item) => ids.has(item.content_id)).map(decorate),
    addLike: async (id) => {
      if (!demoFestivals.some((item) => item.content_id === id))
        throw new Error("축제를 찾을 수 없어요.");
      ids.add(id);
      persist();
    },
    removeLike: async (id) => {
      ids.delete(id);
      persist();
    },
    // 주변 장소 목업을 실제 장소처럼 만들지 않습니다. FE2는 API 모드에서 연결합니다.
    getNearby: async () => ({ items: [], total: 0, page: 1, size: 20 }),
  };
}
