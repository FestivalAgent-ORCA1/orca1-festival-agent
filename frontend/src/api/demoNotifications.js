import { ApiError } from "./client.js";
import { parsePage } from "../lib/format.js";

// 예시 모드의 알림. 실제 알림은 서버 배치가 만들므로, 계정마다 예시 알림 3개를 처음 한 번 넣어 둡니다.
const key = "orca:demo:notifications:v1";

function sample() {
  const daysAgo = (days) =>
    new Date(Date.now() - days * 86400000).toISOString();
  return [
    {
      id: 3,
      type: "FESTIVAL_D1",
      message: "찜한 '부산불꽃축제'가 내일 시작해요!",
      festival_content_id: "demo-busan",
      is_read: false,
      created_at: daysAgo(0),
    },
    {
      id: 2,
      type: "SIMILAR_FESTIVAL",
      message: "'청송사과축제'와 비슷한 '파주장단콩축제'를 찾았어요.",
      festival_content_id: "demo-paju",
      is_read: false,
      created_at: daysAgo(2),
    },
    {
      id: 1,
      type: "FESTIVAL_D7",
      message: "찜한 '청송사과축제'까지 일주일 남았어요.",
      festival_content_id: "demo-apple",
      is_read: true,
      created_at: daysAgo(6),
    },
  ];
}

export function createDemoNotifications(storage, viewer) {
  let byUser = {};
  try {
    const stored = JSON.parse(storage?.getItem(key) || "{}");
    if (stored && typeof stored === "object" && !Array.isArray(stored))
      byUser = stored;
  } catch {
    /* 깨진 값은 비우고 시작합니다 */
  }
  const persist = () => {
    try {
      storage?.setItem(key, JSON.stringify(byUser));
    } catch {
      /* blocked browser storage */
    }
  };
  const mine = async () => {
    const me = await viewer();
    if (!me) throw new ApiError(401, "UNAUTHORIZED", "로그인이 필요해요.");
    if (!byUser[me.id]) {
      byUser[me.id] = sample();
      persist();
    }
    return byUser[me.id];
  };
  return {
    async getNotifications(query = {}) {
      const list = await mine();
      const page = parsePage(query.page);
      const size = Math.min(50, parsePage(query.size || 20));
      return {
        items: list.slice((page - 1) * size, page * size),
        page,
        size,
        total: list.length,
      };
    },
    async getUnreadCount() {
      const list = await mine();
      return { count: list.filter((item) => !item.is_read).length };
    },
    async markRead(id) {
      const item = (await mine()).find((entry) => entry.id === Number(id));
      if (!item)
        throw new ApiError(
          404,
          "NOTIFICATION_NOT_FOUND",
          "알림을 찾을 수 없어요.",
        );
      item.is_read = true;
      persist();
    },
    async markAllRead() {
      (await mine()).forEach((item) => {
        item.is_read = true;
      });
      persist();
    },
  };
}
