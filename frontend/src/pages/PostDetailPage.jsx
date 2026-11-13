import { useCallback, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { repository } from "../api/repository.js";
import { useToast } from "../contexts/ToastContext.jsx";
import { useResource } from "../hooks/useResource.js";
import { postDate } from "../lib/postDate.js";
import CommentList from "../components/community/CommentList.jsx";
import Button from "../components/common/Button.jsx";
import TagChip from "../components/common/TagChip.jsx";
import Loading from "../components/common/Loading.jsx";
import ErrorState from "../components/common/ErrorState.jsx";

export default function PostDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const notify = useToast();
  const load = useCallback((signal) => repository.getPost(id, signal), [id]);
  const post = useResource(load);
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  if (post.status === "loading")
    return <Loading text="글을 불러오고 있어요." />;
  if (post.status === "error")
    return (
      <section className="wrap post-detail">
        <ErrorState
          error={post.error}
          onRetry={post.error?.status === 404 ? undefined : post.retry}
        />
        <p className="back-link">
          <Link to="/community">← 커뮤니티로 돌아가기</Link>
        </p>
      </section>
    );
  const item = post.data;
  const remove = async () => {
    setDeleting(true);
    try {
      await repository.deletePost(item.id);
      notify("글을 삭제했어요.");
      navigate("/community", { replace: true });
    } catch (err) {
      notify(err.message || "글을 삭제하지 못했어요.");
      setDeleting(false);
    }
  };
  return (
    <article className="wrap post-detail">
      <p className="back-link">
        <Link to="/community">← 커뮤니티</Link>
      </p>
      {item.festival && (
        <Link to={`/festivals/${encodeURIComponent(item.festival.content_id)}`}>
          <TagChip>{item.festival.title}</TagChip>
        </Link>
      )}
      <h1>{item.title}</h1>
      <div className="post-meta">
        <span>{item.author.nickname}</span>
        <span>{postDate(item.created_at)}</span>
        {item.updated_at !== item.created_at && <span>수정됨</span>}
        <span>조회 {item.view_count}</span>
      </div>
      <div className="post-body">{item.content}</div>
      {item.is_mine &&
        (confirming ? (
          <div className="post-actions" role="group" aria-label="삭제 확인">
            <span>이 글을 삭제할까요? 댓글도 함께 사라져요.</span>
            <Button className="danger" disabled={deleting} onClick={remove}>
              {deleting ? "삭제하는 중…" : "삭제"}
            </Button>
            <Button variant="white" onClick={() => setConfirming(false)}>
              취소
            </Button>
          </div>
        ) : (
          <div className="post-actions">
            <Button
              variant="white"
              onClick={() =>
                // 수정 화면이 글을 다시 불러오지 않도록(조회수 +1 방지) 현재 글을 넘깁니다.
                navigate(`/community/${item.id}/edit`, { state: { post: item } })
              }
            >
              수정
            </Button>
            <Button variant="white" onClick={() => setConfirming(true)}>
              삭제
            </Button>
          </div>
        ))}
      <CommentList key={item.id} postId={item.id} />
    </article>
  );
}
