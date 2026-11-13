import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { repository } from "../../api/repository.js";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { useToast } from "../../contexts/ToastContext.jsx";
import { useResource } from "../../hooks/useResource.js";
import { postDate } from "../../lib/postDate.js";
import Button from "../common/Button.jsx";
import Loading from "../common/Loading.jsx";
import ErrorState from "../common/ErrorState.jsx";

// 글 상세 아래의 댓글 목록과 입력 칸. 부모에서 key={postId}로 그려 주세요.
export default function CommentList({ postId }) {
  const { status } = useAuth();
  const notify = useToast();
  const load = useCallback(
    (signal) => repository.getComments(postId, signal),
    [postId],
  );
  const comments = useResource(load);
  // 쓰기·삭제 후에는 다시 불러오지 않고 화면의 목록만 고칩니다.
  const [changed, setChanged] = useState(null);
  const list = changed ?? comments.data ?? [];
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault();
    if (!text.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      const comment = await repository.createComment(postId, text.trim());
      setChanged([...list, comment]);
      setText("");
    } catch (err) {
      setError(err.message || "댓글을 남기지 못했어요.");
    } finally {
      setSubmitting(false);
    }
  };
  const remove = async (id) => {
    try {
      await repository.deleteComment(id);
      setChanged(list.filter((item) => item.id !== id));
      notify("댓글을 삭제했어요.");
    } catch (err) {
      notify(err.message || "댓글을 삭제하지 못했어요.");
    }
  };
  const here = `/community/${postId}`;
  return (
    <section className="comments" aria-label="댓글">
      <h2>댓글 {comments.status === "success" ? list.length : ""}</h2>
      {comments.status === "loading" ? (
        <Loading text="댓글을 불러오고 있어요." />
      ) : comments.status === "error" ? (
        <ErrorState
          error={comments.error}
          onRetry={() => {
            setChanged(null);
            comments.retry();
          }}
        />
      ) : list.length ? (
        <ul className="comment-list">
          {list.map((comment) => (
            <li key={comment.id} className="comment">
              <div className="comment-meta">
                <strong>{comment.author.nickname}</strong>
                <span>{postDate(comment.created_at)}</span>
                {comment.is_mine && (
                  <button
                    type="button"
                    className="text-button comment-delete"
                    onClick={() => remove(comment.id)}
                  >
                    삭제
                  </button>
                )}
              </div>
              <p>{comment.content}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="comment-empty">첫 댓글을 남겨보세요.</p>
      )}
      {status === "authenticated" ? (
        <form className="comment-form" onSubmit={submit}>
          <label className="sr-only" htmlFor="comment-text">
            댓글 내용
          </label>
          <textarea
            id="comment-text"
            rows={3}
            maxLength={1000}
            placeholder="따뜻한 한마디를 남겨주세요."
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}
          <Button
            variant="blue"
            type="submit"
            disabled={submitting || !text.trim()}
          >
            {submitting ? "남기는 중…" : "댓글 남기기"}
          </Button>
        </form>
      ) : (
        <p className="comment-login">
          <Link to={`/login?redirect=${encodeURIComponent(here)}`}>
            로그인
          </Link>
          하고 댓글을 남겨보세요.
        </p>
      )}
    </section>
  );
}
