import { ApiError } from "./client.js";
import { demoFestivals } from "../data/festivals.js";
import { parsePage } from "../lib/format.js";

// 예시 모드의 커뮤니티. 글과 댓글은 이 브라우저에만 저장합니다.
// viewer()는 로그인한 예시 계정을 돌려주거나, 비로그인이면 null을 돌려줍니다.
const key = "orca:demo:community:v1";
const sampleAuthor = { id: 0, nickname: "주말여행자" };

function seed() {
  return {
    nextId: 4,
    posts: [
      {
        id: 1,
        title: "부산불꽃축제 자리 잡기 팁 있을까요?",
        content:
          "올해 처음 가보려고 해요. 광안리 해변 쪽은 몇 시쯤 가야 자리를 잡을 수 있을까요?\n돗자리 말고 챙기면 좋은 것도 알려주세요!",
        author: sampleAuthor,
        festival_content_id: "demo-busan",
        view_count: 24,
        created_at: "2026-11-02T10:00:00+09:00",
        updated_at: "2026-11-02T10:00:00+09:00",
      },
      {
        id: 2,
        title: "청송사과축제 다녀왔어요",
        content:
          "사과 따기 체험이 생각보다 재밌었어요. 주차장이 일찍 차니까 대중교통이나 셔틀을 추천해요.",
        author: { id: 0, nickname: "사과러버" },
        festival_content_id: "demo-apple",
        view_count: 11,
        created_at: "2026-11-05T15:30:00+09:00",
        updated_at: "2026-11-05T15:30:00+09:00",
      },
    ],
    comments: [
      {
        id: 3,
        post_id: 1,
        content: "오후 3시 전에는 가야 앞쪽에 앉을 수 있었어요. 담요 꼭 챙기세요!",
        author: { id: 0, nickname: "불꽃구경" },
        created_at: "2026-11-02T12:10:00+09:00",
      },
    ],
  };
}

export function createDemoCommunity(storage, viewer) {
  let data = seed();
  try {
    const stored = JSON.parse(storage?.getItem(key) || "null");
    if (Array.isArray(stored?.posts) && Array.isArray(stored?.comments))
      data = stored;
  } catch {
    /* 깨진 값은 예시 글로 다시 시작합니다 */
  }
  const persist = () => {
    try {
      storage?.setItem(key, JSON.stringify(data));
    } catch {
      /* blocked browser storage */
    }
  };
  const nextId = () => data.nextId++;
  const now = () => new Date().toISOString();
  const festivalOf = (id) => {
    const item = demoFestivals.find((festival) => festival.content_id === id);
    return item ? { content_id: item.content_id, title: item.title } : null;
  };
  const findPost = (id) => {
    const post = data.posts.find((item) => item.id === Number(id));
    if (!post) throw new ApiError(404, "POST_NOT_FOUND", "글을 찾을 수 없어요.");
    return post;
  };
  const toPost = (post, me, full) => ({
    id: post.id,
    title: post.title,
    content: full ? post.content : post.content.slice(0, 100),
    author: post.author,
    festival: festivalOf(post.festival_content_id),
    view_count: post.view_count,
    comment_count: data.comments.filter((item) => item.post_id === post.id)
      .length,
    is_mine: Boolean(me) && post.author.id === me.id,
    created_at: post.created_at,
    updated_at: post.updated_at,
  });
  const toComment = (comment, me) => ({
    id: comment.id,
    content: comment.content,
    author: comment.author,
    is_mine: Boolean(me) && comment.author.id === me.id,
    created_at: comment.created_at,
  });
  const requireMe = async () => {
    const me = await viewer();
    if (!me) throw new ApiError(401, "UNAUTHORIZED", "로그인이 필요해요.");
    return me;
  };
  const requireOwner = (item, me) => {
    if (item.author.id !== me.id)
      throw new ApiError(403, "FORBIDDEN", "내가 쓴 글만 바꿀 수 있어요.");
  };
  const invalid = (message) => new ApiError(422, "VALIDATION_ERROR", message);
  const checkPost = ({ title = "", content = "" }) => {
    if (!title.trim() || title.trim().length > 100)
      throw invalid("제목은 1~100자로 입력해 주세요.");
    if (!content.trim()) throw invalid("내용을 입력해 주세요.");
    return { title: title.trim(), content: content.trim() };
  };
  return {
    async getPosts(query = {}) {
      const me = await viewer();
      const page = parsePage(query.page);
      const size = Math.min(50, parsePage(query.size || 20));
      const found = data.posts
        .filter(
          (post) =>
            !query.festival_content_id ||
            post.festival_content_id === query.festival_content_id,
        )
        .toSorted((a, b) => b.id - a.id);
      return {
        items: found
          .slice((page - 1) * size, page * size)
          .map((post) => toPost(post, me, false)),
        page,
        size,
        total: found.length,
      };
    },
    async getPost(id) {
      const me = await viewer();
      const post = findPost(id);
      post.view_count += 1;
      persist();
      return toPost(post, me, true);
    },
    async createPost(body) {
      const me = await requireMe();
      const post = {
        id: nextId(),
        ...checkPost(body),
        author: { id: me.id, nickname: me.nickname },
        festival_content_id: body.festival_content_id || null,
        view_count: 0,
        created_at: now(),
        updated_at: now(),
      };
      data.posts.push(post);
      persist();
      return toPost(post, me, true);
    },
    async updatePost(id, body) {
      const me = await requireMe();
      const post = findPost(id);
      requireOwner(post, me);
      Object.assign(post, checkPost(body), {
        festival_content_id: body.festival_content_id || null,
        updated_at: now(),
      });
      persist();
      return toPost(post, me, true);
    },
    async deletePost(id) {
      const me = await requireMe();
      const post = findPost(id);
      requireOwner(post, me);
      data.posts = data.posts.filter((item) => item !== post);
      data.comments = data.comments.filter((item) => item.post_id !== post.id);
      persist();
    },
    async getComments(id) {
      const me = await viewer();
      const post = findPost(id);
      return data.comments
        .filter((item) => item.post_id === post.id)
        .map((comment) => toComment(comment, me));
    },
    async createComment(id, content = "") {
      const me = await requireMe();
      const post = findPost(id);
      const text = content.trim();
      if (!text || text.length > 1000)
        throw invalid("댓글은 1~1000자로 입력해 주세요.");
      const comment = {
        id: nextId(),
        post_id: post.id,
        content: text,
        author: { id: me.id, nickname: me.nickname },
        created_at: now(),
      };
      data.comments.push(comment);
      persist();
      return toComment(comment, me);
    },
    async deleteComment(id) {
      const me = await requireMe();
      const comment = data.comments.find((item) => item.id === Number(id));
      if (!comment)
        throw new ApiError(404, "COMMENT_NOT_FOUND", "댓글을 찾을 수 없어요.");
      requireOwner(comment, me);
      data.comments = data.comments.filter((item) => item !== comment);
      persist();
    },
  };
}
