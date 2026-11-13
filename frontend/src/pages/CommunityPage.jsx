import { useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { repository } from "../api/repository.js";
import { useAuth } from "../contexts/AuthContext.jsx";
import { useResource } from "../hooks/useResource.js";
import { parsePage } from "../lib/format.js";
import PostItem from "../components/community/PostItem.jsx";
import Button from "../components/common/Button.jsx";
import Loading from "../components/common/Loading.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import EmptyState from "../components/common/EmptyState.jsx";

const PAGE_SIZE = 10;

export default function CommunityPage() {
  const { status } = useAuth();
  const [params, setParams] = useSearchParams();
  const page = parsePage(params.get("page"));
  // 축제 상세 등에서 /community?festival=<content_id>로 오면 그 축제 글만 보여줍니다.
  const festival = params.get("festival") || "";
  const load = useCallback(
    (signal) =>
      repository.getPosts(
        { page, size: PAGE_SIZE, festival_content_id: festival },
        signal,
      ),
    [page, festival],
  );
  const posts = useResource(load);
  const writeTo = festival
    ? `/community/write?festival=${encodeURIComponent(festival)}`
    : "/community/write";
  const lastPage = Math.max(1, Math.ceil((posts.data?.total || 0) / PAGE_SIZE));
  const goPage = (next) =>
    setParams((previous) => {
      const query = new URLSearchParams(previous);
      query.set("page", String(next));
      return query;
    });
  return (
    <section className="wrap community-page">
      <div className="community-head">
        <div className="page-intro">
          <span className="eyebrow">WEEKEND TALK</span>
          <h1 className="display">축제 이야기, 한 장씩.</h1>
          <p>다녀온 축제의 팁과 후기를 나눠요.</p>
        </div>
        <Button
          as={Link}
          variant="blue"
          to={
            status === "authenticated"
              ? writeTo
              : `/login?redirect=${encodeURIComponent(writeTo)}`
          }
        >
          글쓰기
        </Button>
      </div>
      {festival && (
        <p className="community-filter">
          {posts.data?.items[0]?.festival?.title || "선택한 축제"} 이야기만 보는
          중 · <Link to="/community">전체 보기</Link>
        </p>
      )}
      {posts.status === "loading" ? (
        <Loading text="축제 이야기를 불러오고 있어요." />
      ) : posts.status === "error" ? (
        <ErrorState error={posts.error} onRetry={posts.retry} />
      ) : posts.data.items.length ? (
        <>
          <div className="post-list">
            {posts.data.items.map((post) => (
              <PostItem key={post.id} post={post} />
            ))}
          </div>
          {lastPage > 1 && (
            <nav className="pagination" aria-label="글 목록 페이지">
              <Button disabled={page <= 1} onClick={() => goPage(page - 1)}>
                이전
              </Button>
              <span>
                {page} / {lastPage}
              </span>
              <Button
                disabled={page >= lastPage}
                onClick={() => goPage(page + 1)}
              >
                다음
              </Button>
            </nav>
          )}
        </>
      ) : (
        <EmptyState title="아직 올라온 이야기가 없어요.">
          첫 번째 축제 이야기를 남겨보세요.
        </EmptyState>
      )}
    </section>
  );
}
