export default function Loading({ text = "좋아하는 장면을 찾고 있어요." }) {
  return (
    <div className="loading-state" role="status">
      <span className="loading-flower" aria-hidden="true">
        ✳
      </span>
      <span>{text}</span>
    </div>
  );
}
