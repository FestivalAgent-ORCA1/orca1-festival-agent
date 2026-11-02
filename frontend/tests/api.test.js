import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { createApiClient, ApiError } from "../src/api/client.js";
import { createFestivalApi } from "../src/api/festivals.js";
import { createLikesApi } from "../src/api/likes.js";
import { createPlacesApi } from "../src/api/places.js";

test("실제 HTTP 요청이 snake_case 필터, JWT, 상세 ID를 API 규격대로 보낸다", async () => {
  const seen = [];
  const server = http.createServer(async (request, response) => {
    let body = "";
    for await (const chunk of request) body += chunk;
    seen.push({
      url: new URL(request.url, "http://localhost"),
      authorization: request.headers.authorization,
      method: request.method,
      body,
    });
    response.setHeader("Content-Type", "application/json");
    if (request.method === "DELETE") {
      response.writeHead(204).end();
      return;
    }
    if (request.method === "POST") {
      response.writeHead(201).end("{}");
      return;
    }
    response.end(JSON.stringify({ items: [], page: 1, size: 20, total: 0 }));
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const request = createApiClient({
      baseUrl: `http://127.0.0.1:${server.address().port}/`,
      getToken: () => "test-token",
    });
    const festivals = createFestivalApi(request),
      likes = createLikesApi(request),
      places = createPlacesApi(request);
    await festivals.getFestivals({
      area_code: ["1", "31"],
      tags: ["night", "food"],
      keyword: "빛 축제",
      page: 2,
      size: 12,
      empty: "",
    });
    assert.equal(seen[0].url.pathname, "/api/festivals");
    assert.equal(seen[0].url.searchParams.get("area_code"), "1,31");
    assert.equal(seen[0].url.searchParams.get("tags"), "night,food");
    assert.equal(seen[0].url.searchParams.get("keyword"), "빛 축제");
    assert.equal(seen[0].url.searchParams.get("page"), "2");
    assert.equal(seen[0].url.searchParams.has("empty"), false);
    assert.equal(seen[0].authorization, "Bearer test-token");
    await festivals.getDetail("id/with space");
    assert.equal(seen[1].url.pathname, "/api/festivals/id%2Fwith%20space");
    await festivals.getSimilar("123");
    assert.equal(seen[2].url.pathname, "/api/festivals/123/similar");
    await festivals.getRecommended();
    assert.equal(seen[3].url.pathname, "/api/festivals/recommended");
    assert.equal(seen[3].url.searchParams.get("size"), "3");
    await likes.addLike("123");
    assert.deepEqual(JSON.parse(seen[4].body), { content_id: "123" });
    assert.equal(seen[4].method, "POST");
    await likes.removeLike("123");
    assert.equal(seen[5].method, "DELETE");
    await places.getNearby({ content_id: "123", category: "cafe", page: 1 });
    assert.equal(seen[6].url.searchParams.get("content_id"), "123");
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("로그인 안 한 목록 요청에는 Authorization 헤더를 만들지 않는다", async () => {
  const request = createApiClient({
    fetcher: async (_url, options) => {
      assert.equal(options.headers.Authorization, undefined);
      return Response.json({ items: [], total: 0 });
    },
  });
  await request("/api/festivals");
});

test("401은 인증 만료 처리를 실행하고 서버의 오류를 유지한다", async () => {
  let expired = 0;
  const request = createApiClient({
    onUnauthorized: () => expired++,
    fetcher: async () =>
      Response.json(
        { code: "UNAUTHORIZED", message: "로그인이 필요해요." },
        { status: 401 },
      ),
  });
  await assert.rejects(
    request("/api/likes"),
    (error) =>
      error instanceof ApiError &&
      error.status === 401 &&
      error.message === "로그인이 필요해요.",
  );
  assert.equal(expired, 1);
});

test("찜 중복 409만 성공으로 취급하며 다른 서버 오류는 보존한다", async () => {
  let code = "ALREADY_LIKED";
  const likes = createLikesApi(
    createApiClient({
      fetcher: async () =>
        Response.json({ code, message: "실패" }, { status: 409 }),
    }),
  );
  await likes.addLike("123");
  code = "OTHER_CONFLICT";
  await assert.rejects(
    likes.addLike("123"),
    (error) => error.code === "OTHER_CONFLICT",
  );
});

test("찜 목록 50개를 넘으면 뒷 페이지도 읽고 중복은 제거한다", async () => {
  const pages = [];
  const likes = createLikesApi(async (_path, { query }) => {
    pages.push(query.page);
    return query.page === 1
      ? {
          items: Array.from({ length: 50 }, (_, id) => ({
            content_id: String(id),
          })),
          total: 52,
        }
      : { items: [{ content_id: "49" }, { content_id: "50" }], total: 52 };
  });
  const result = await likes.getLikes();
  assert.deepEqual(pages, [1, 2]);
  assert.equal(result.length, 51);
});

test("연결 실패와 잘못된 JSON을 예시 데이터로 숨기지 않는다", async () => {
  const request = createApiClient({
    fetcher: async () => {
      throw new TypeError("offline");
    },
  });
  await assert.rejects(
    request("/api/festivals"),
    (error) => error.code === "NETWORK_ERROR",
  );
  const invalid = createApiClient({
    fetcher: async () => new Response("<html>not json</html>"),
  });
  await assert.rejects(
    invalid("/api/festivals"),
    (error) => error.code === "INVALID_RESPONSE",
  );
});

test("요청 취소와 서버 지연을 구분한다", async () => {
  const fetcher = (_url, { signal }) =>
    new Promise((_resolve, reject) => {
      const abort = () => reject(new DOMException("Aborted", "AbortError"));
      if (signal.aborted) abort();
      else signal.addEventListener("abort", abort, { once: true });
    });
  const request = createApiClient({ fetcher, timeoutMs: 10 });
  await assert.rejects(
    request("/api/festivals"),
    (error) => error.code === "TIMEOUT",
  );
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(
    request("/api/festivals", { signal: controller.signal }),
    (error) => error.name === "AbortError",
  );
});
