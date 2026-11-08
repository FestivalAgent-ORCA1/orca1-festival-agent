import test from "node:test";
import assert from "node:assert/strict";
import { filterFestivals, createDemoRepository } from "../src/api/demo.js";
import { demoFestivals } from "../src/data/festivals.js";
import {
  safeExternalUrl,
  plainText,
  dateLabel,
  festivalStatus,
  parsePage,
} from "../src/lib/format.js";

test("지역·태그·검색어를 함께 적용하며 페이지 total을 유지한다", () => {
  const result = filterFestivals(demoFestivals, {
    keyword: "사 과",
    area_code: "35",
    tags: "night,food",
  });
  assert.deepEqual(
    result.items.map((item) => item.content_id),
    ["demo-apple"],
  );
  assert.equal(filterFestivals(demoFestivals, { area_code: "1" }).total, 0);
  const page = filterFestivals(demoFestivals, { page: 2, size: 1 });
  assert.equal(page.total, 3);
  assert.equal(page.items.length, 1);
  assert.equal(page.items[0].content_id, "demo-busan");
});
test("날짜 범위는 축제 시작~종료가 겹치는 기준으로 고른다", () => {
  const result = filterFestivals(demoFestivals, {
    start_date: "2026-11-08",
    end_date: "2026-11-08",
  });
  assert.deepEqual(
    result.items.map((item) => item.content_id),
    ["demo-apple"],
  );
});
test("찜을 다시 읽고 해제하며 잘못 저장된 ID는 버린다", async () => {
  const saved = new Map([
    ["orca:demo:likes:v1", '["demo-busan","unknown","demo-busan"]'],
  ]);
  const storage = {
    getItem: (key) => saved.get(key),
    setItem: (key, value) => saved.set(key, value),
  };
  const repository = createDemoRepository(storage);
  assert.equal((await repository.getLikes()).length, 1);
  await repository.addLike("demo-apple");
  const reloaded = createDemoRepository(storage);
  assert.equal((await reloaded.getLikes()).length, 2);
  await reloaded.removeLike("demo-busan");
  assert.deepEqual(
    (await reloaded.getLikes()).map((item) => item.content_id),
    ["demo-apple"],
  );
  await assert.rejects(reloaded.addLike("not-a-festival"));
});
test("저장소 접근이 막혀도 화면은 작동하며 저장 제한을 보고한다", async () => {
  const repository = createDemoRepository({
    getItem() {
      throw new Error("blocked");
    },
    setItem() {
      throw new Error("blocked");
    },
  });
  await repository.addLike("demo-busan");
  assert.equal((await repository.getLikes()).length, 1);
  assert.equal(repository.storageWarning, true);
});
test("없는 축제는 404이며 찜·목록과 같은 응답 필드를 쓴다", async () => {
  const repository = createDemoRepository();
  await assert.rejects(
    repository.getDetail("invalid"),
    (error) => error.status === 404,
  );
  const item = await repository.getDetail("demo-busan");
  assert.equal(item.content_id, "demo-busan");
  assert.ok(item.overview);
  assert.ok(item.tags.includes("night"));
});
test("서버의 HTML 소개와 외부 URL을 실행 가능한 코드로 넣지 않는다", () => {
  assert.equal(safeExternalUrl("javascript:alert(1)"), null);
  assert.equal(
    safeExternalUrl("data:text/html,<script>alert(1)</script>"),
    null,
  );
  assert.equal(
    safeExternalUrl("https://example.com/info"),
    "https://example.com/info",
  );
  assert.equal(
    plainText("<p>축제 &amp; 하루<br />안내</p>"),
    "축제 & 하루\n안내",
  );
});
test("일정의 날짜·종료 상태를 한국 날짜 기준 문자열로 처리한다", () => {
  assert.equal(dateLabel("2026-11-07", "2026-11-07"), "11.07");
  assert.equal(
    festivalStatus(
      { start_date: "2026-11-04", end_date: "2026-11-08" },
      "2026-11-08",
    ),
    "ongoing",
  );
  assert.equal(
    festivalStatus(
      { start_date: "2026-11-04", end_date: "2026-11-08" },
      "2026-11-09",
    ),
    "ended",
  );
});
test("손으로 입력한 잘못된 페이지 값은 유효한 페이지로 제한한다", () => {
  for (const input of ["NaN", "Infinity", "-3", "abc", null])
    assert.equal(parsePage(input), 1);
  assert.equal(parsePage("2.8"), 2);
});
