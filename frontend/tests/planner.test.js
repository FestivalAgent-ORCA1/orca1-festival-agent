import test from "node:test";
import assert from "node:assert/strict";
import { buildHistory, lastItinerary, normalizeBlocks } from "../src/lib/chat.js";
import { toMinutes, toTime, toSchedulePayload, visitDateLabel, placeIdsOf } from "../src/lib/itinerary.js";
import { buildDemoItinerary, createPlannerDemo, demoChatReply } from "../src/api/plannerDemo.js";
import { createAgentApi } from "../src/api/agent.js";

const festival = { content_id: "1", title: "빛초롱" };

test("모르는 블록·잘못된 블록은 버리고 선택지는 마지막 하나만 남긴다", () => {
  const blocks = normalizeBlocks([
    { type: "quick_replies", options: [{ label: "a", message: "a" }] },
    { type: "text", text: "안녕" },
    { type: "map_v2", foo: 1 },
    { type: "text", text: "  " },
    { type: "festival_cards", items: [{ festival, reason: "" }, { festival: {} }] },
    { type: "quick_replies", options: [1, 2, 3, 4, 5].map((n) => ({ label: `${n}`, message: `${n}` })) },
  ]);
  assert.deepEqual(blocks.map((b) => b.type), ["text", "festival_cards", "quick_replies"]);
  assert.equal(blocks[1].items.length, 1);
  assert.equal(blocks[1].items[0].reason, null);
  assert.equal(blocks[2].options.length, 4);
  assert.deepEqual(normalizeBlocks(null), []);
});

test("history는 글만, 로컬 메시지·오류 제외, 최근 10개", () => {
  const messages = [
    { role: "assistant", local: true, blocks: [{ type: "text", text: "인사" }] },
    ...Array.from({ length: 6 }, (_, i) => [
      { role: "user", text: `q${i}` },
      { role: "assistant", blocks: [{ type: "text", text: `a${i}` }, { type: "festival_cards", items: [] }] },
    ]).flat(),
    { role: "error", error: {} },
  ];
  const history = buildHistory(messages);
  assert.equal(history.length, 10);
  assert.deepEqual(history.at(-1), { role: "assistant", text: "a5" });
  assert.ok(!history.some((h) => h.text === "인사"));
});

test("마지막 timeline 블록의 itinerary를 찾는다", () => {
  const a = { items: [], visit_date: "2026-11-01" };
  const b = { items: [], visit_date: "2026-11-02" };
  const messages = [
    { role: "assistant", blocks: [{ type: "timeline", itinerary: a }] },
    { role: "user", text: "x" },
    { role: "assistant", blocks: [{ type: "timeline", itinerary: b }, { type: "text", text: "y" }] },
  ];
  assert.equal(lastItinerary(messages), b);
  assert.equal(lastItinerary([]), null);
});

test("시각 변환과 날짜 표시", () => {
  assert.equal(toMinutes("09:30"), 570);
  assert.equal(toTime(570), "09:30");
  assert.ok(Number.isNaN(toMinutes("25:00")));
  assert.equal(visitDateLabel("2026-11-02"), "11월 2일 (월)");
});

test("저장 요청에는 warnings가 없고 title이 들어간다", () => {
  const itinerary = buildDemoItinerary({ festival_content_id: "demo-apple", visit_date: "2026-11-05" });
  const payload = toSchedulePayload(itinerary, "  사과 여행 ");
  assert.equal(payload.title, "사과 여행");
  assert.equal("warnings" in payload, false);
  assert.equal(payload.items.length, itinerary.items.length);
  // 다시 계산할 때 유지할 장소: 축제 자신은 빼고 방문 순서대로
  assert.deepEqual(placeIdsOf(itinerary), ["demo-lunch", "demo-walk", "demo-cafe", "demo-dinner"]);
});

test("예시 시간표는 시간 안에 들어오고 축제를 항상 포함한다", () => {
  const long = buildDemoItinerary({ festival_content_id: "demo-apple", visit_date: "2026-11-05" });
  assert.equal(long.items.length, 5);
  const short = buildDemoItinerary({
    festival_content_id: "demo-apple",
    visit_date: "2026-11-05",
    start_time: "15:00",
    end_time: "18:00",
  });
  assert.ok(short.items.some((item) => item.category === "festival"));
  assert.ok(toMinutes(short.items.at(-1).end_time) <= toMinutes("18:00"));
  assert.throws(
    () => buildDemoItinerary({ festival_content_id: "demo-apple", visit_date: "2026-12-01" }),
    (error) => error.code === "VISIT_DATE_OUT_OF_RANGE",
  );
  assert.throws(
    () => buildDemoItinerary({ festival_content_id: "demo-apple", visit_date: "2026-11-05", start_time: "10:00", end_time: "11:00" }),
    (error) => error.code === "TIME_TOO_SHORT",
  );
});

test("예시 채팅: 축제 없이 일정 요청 → 되묻기, 축제 이름 → 시간표, 수정 요청 반영", () => {
  const ask = demoChatReply({ message: "일정 짜줘" });
  assert.deepEqual(ask.blocks.map((b) => b.type), ["text", "quick_replies"]);
  const plan = demoChatReply({ message: "청송사과축제 11월 5일 일정 짜줘" });
  const timeline = plan.blocks.find((b) => b.type === "timeline");
  assert.equal(timeline.itinerary.visit_date, "2026-11-05");
  const edited = demoChatReply({ message: "18시까지 끝나게 바꿔줘", context: { itinerary: timeline.itinerary } });
  const next = edited.blocks.find((b) => b.type === "timeline");
  assert.equal(next.itinerary.end_time, "18:00");
  assert.equal(next.itinerary.visit_date, "2026-11-05");
  const other = demoChatReply({ message: "다른 축제도 추천해줘", context: { itinerary: timeline.itinerary } });
  assert.equal(other.blocks.find((b) => b.type === "festival_cards").items.length, 3);
});

test("예시 일정 저장·수정·삭제", async () => {
  const store = new Map();
  const storage = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, v) };
  const demo = createPlannerDemo(storage);
  const itinerary = buildDemoItinerary({ festival_content_id: "demo-apple", visit_date: "2026-11-05" });
  const created = await demo.createSchedule({ ...itinerary, title: "사과" });
  assert.equal(created.festival.title, "청송사과축제");
  assert.equal((await demo.getSchedules())[0].item_count, 5);
  await demo.updateSchedule(created.id, { ...itinerary, end_time: "18:00", title: "사과2" });
  assert.equal((await demo.getSchedule(created.id)).title, "사과2");
  await demo.deleteSchedule(created.id);
  await assert.rejects(demo.getSchedule(created.id), (error) => error.status === 404);
});

test("채팅 API는 30초 제한을 넘기면 TIMEOUT으로 바꾼다", async () => {
  const request = (path, { signal }) =>
    new Promise((_, reject) => signal.addEventListener("abort", () => reject(new Error("aborted"))));
  const api = createAgentApi(request, { timeoutMs: 20 });
  await assert.rejects(api.chat({ message: "hi" }), (error) => error.code === "TIMEOUT");
});

test("채팅 API는 응답 블록을 정리하고 요청 본문을 명세대로 보낸다", async () => {
  let sent;
  const request = async (path, options) => {
    sent = { path, ...options };
    return { intent: "smalltalk", blocks: [{ type: "text", text: "안녕" }, { type: "unknown" }] };
  };
  const reply = await createAgentApi(request).chat({ message: "hi", history: [], context: { festival_content_id: null } });
  assert.equal(sent.path, "/api/agent/chat");
  assert.equal(sent.method, "POST");
  assert.deepEqual(Object.keys(sent.body), ["message", "history", "context"]);
  assert.deepEqual(reply.blocks, [{ type: "text", text: "안녕" }]);
});
