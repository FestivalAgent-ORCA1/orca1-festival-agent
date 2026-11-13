import test from "node:test";
import assert from "node:assert/strict";
import { createNotificationsApi } from "../src/api/notifications.js";
import { createDemoNotifications } from "../src/api/demoNotifications.js";

function memoryStorage() {
  const data = new Map();
  return {
    getItem: (key) => (data.has(key) ? data.get(key) : null),
    setItem: (key, value) => data.set(key, String(value)),
  };
}

test("알림 API가 명세의 주소와 메서드로 요청한다", async () => {
  const seen = [];
  const request = async (path, options = {}) => {
    seen.push(`${options.method || "GET"} ${path}`);
    return {};
  };
  const api = createNotificationsApi(request);
  await api.getNotifications({ page: 1 });
  await api.getUnreadCount();
  await api.markRead(41);
  await api.markAllRead();
  assert.deepEqual(seen, [
    "GET /api/notifications",
    "GET /api/notifications/unread-count",
    "PATCH /api/notifications/41/read",
    "PATCH /api/notifications/read-all",
  ]);
});

test("예시 알림은 계정별로 읽음 상태를 저장한다", async () => {
  const storage = memoryStorage();
  let viewer = { id: 1, nickname: "가나" };
  const demo = createDemoNotifications(storage, async () => viewer);
  const { items } = await demo.getNotifications({});
  assert.equal((await demo.getUnreadCount()).count, 2);
  await demo.markRead(items[0].id);
  assert.equal((await demo.getUnreadCount()).count, 1);
  // 다른 계정의 읽음 상태는 따로
  viewer = { id: 2, nickname: "다라" };
  assert.equal((await demo.getUnreadCount()).count, 2);
  await demo.markAllRead();
  assert.equal((await demo.getUnreadCount()).count, 0);
  // 새로고침해도 유지
  viewer = { id: 1, nickname: "가나" };
  const reloaded = createDemoNotifications(storage, async () => viewer);
  assert.equal((await reloaded.getUnreadCount()).count, 1);
  viewer = null;
  await assert.rejects(reloaded.getNotifications({}), { status: 401 });
});
