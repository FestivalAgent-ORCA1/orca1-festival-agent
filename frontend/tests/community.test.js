import test from "node:test";
import assert from "node:assert/strict";
import { createPostsApi } from "../src/api/posts.js";
import { createDemoCommunity } from "../src/api/demoCommunity.js";

function memoryStorage() {
  const data = new Map();
  return {
    getItem: (key) => (data.has(key) ? data.get(key) : null),
    setItem: (key, value) => data.set(key, String(value)),
  };
}

test("커뮤니티 API가 명세의 주소와 메서드로 요청한다", async () => {
  const seen = [];
  const request = async (path, options = {}) => {
    seen.push(`${options.method || "GET"} ${path}`);
    return {};
  };
  const posts = createPostsApi(request);
  await posts.getPosts({ page: 1 });
  await posts.getPost(12);
  await posts.createPost({ title: "제목", content: "내용" });
  await posts.updatePost(12, { title: "제목", content: "내용" });
  await posts.deletePost(12);
  await posts.getComments(12);
  await posts.createComment(12, "댓글");
  await posts.deleteComment(7);
  assert.deepEqual(seen, [
    "GET /api/posts",
    "GET /api/posts/12",
    "POST /api/posts",
    "PUT /api/posts/12",
    "DELETE /api/posts/12",
    "GET /api/posts/12/comments",
    "POST /api/posts/12/comments",
    "DELETE /api/comments/7",
  ]);
});

test("예시 커뮤니티에서 글쓰기·댓글·수정·삭제가 작성자 기준으로 동작한다", async () => {
  const storage = memoryStorage();
  const me = { id: 7, nickname: "축제러버" };
  let viewer = me;
  const demo = createDemoCommunity(storage, async () => viewer);
  const before = await demo.getPosts({});
  const post = await demo.createPost({
    title: " 첫 글 ",
    content: "가".repeat(150),
    festival_content_id: "demo-busan",
  });
  assert.equal(post.title, "첫 글");
  assert.equal(post.is_mine, true);
  assert.equal(post.festival.title, "부산불꽃축제");
  const list = await demo.getPosts({});
  assert.equal(list.total, before.total + 1);
  assert.equal(list.items[0].id, post.id, "최신 글이 먼저 온다");
  assert.equal(list.items[0].content.length, 100, "목록은 앞 100자만");
  const comment = await demo.createComment(post.id, "좋아요");
  assert.equal((await demo.getPost(post.id)).comment_count, 1);
  // 다른 사람은 수정·삭제할 수 없다
  viewer = { id: 8, nickname: "다른사람" };
  assert.equal((await demo.getPost(post.id)).is_mine, false);
  await assert.rejects(demo.deletePost(post.id), { status: 403 });
  await assert.rejects(demo.deleteComment(comment.id), { status: 403 });
  viewer = null;
  await assert.rejects(demo.createComment(post.id, "몰래"), { status: 401 });
  // 새로고침해도 남아 있고, 작성자는 지울 수 있다
  viewer = me;
  const reloaded = createDemoCommunity(storage, async () => viewer);
  await reloaded.updatePost(post.id, { title: "고친 글", content: "내용" });
  assert.equal((await reloaded.getPost(post.id)).title, "고친 글");
  await reloaded.deletePost(post.id);
  await assert.rejects(reloaded.getPost(post.id), { status: 404 });
  assert.deepEqual(await reloaded.getComments(1).then((items) => items.length), 1);
});

test("축제별로 글을 거르고 빈 제목은 막는다", async () => {
  const demo = createDemoCommunity(memoryStorage(), async () => ({
    id: 1,
    nickname: "가나",
  }));
  const busan = await demo.getPosts({ festival_content_id: "demo-busan" });
  assert.ok(busan.items.every((post) => post.festival?.content_id === "demo-busan"));
  await assert.rejects(demo.createPost({ title: "  ", content: "내용" }), {
    status: 422,
  });
});
