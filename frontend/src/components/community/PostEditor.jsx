import { useState } from "react";
import Button from "../common/Button.jsx";
import TagChip from "../common/TagChip.jsx";

// 글쓰기·수정 공용 입력 칸. onSubmit이 오류를 던지면 메시지를 보여줍니다.
export default function PostEditor({
  initial = { title: "", content: "" },
  festival,
  onRemoveFestival,
  submitLabel,
  onSubmit,
}) {
  const [title, setTitle] = useState(initial.title);
  const [content, setContent] = useState(initial.content);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault();
    if (!title.trim() || !content.trim()) {
      setError("제목과 내용을 모두 입력해 주세요.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await onSubmit({ title: title.trim(), content: content.trim() });
    } catch (err) {
      setError(err.message || "저장하지 못했어요. 다시 시도해 주세요.");
      setSubmitting(false);
    }
  };
  return (
    <form className="auth-form" onSubmit={submit}>
      {festival && (
        <div className="festival-chip-row">
          관련 축제 <TagChip>{festival.title}</TagChip>
          {onRemoveFestival && (
            <button
              type="button"
              className="text-button"
              onClick={onRemoveFestival}
            >
              연결 해제
            </button>
          )}
        </div>
      )}
      <label className="auth-field">
        <span>
          제목 <span className="auth-hint">{title.length}/100</span>
        </span>
        <input
          type="text"
          required
          maxLength={100}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </label>
      <label className="auth-field">
        내용
        <textarea
          required
          rows={10}
          value={content}
          onChange={(event) => setContent(event.target.value)}
        />
      </label>
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
      <Button variant="blue" type="submit" disabled={submitting}>
        {submitting ? "저장하는 중…" : submitLabel}
      </Button>
    </form>
  );
}
