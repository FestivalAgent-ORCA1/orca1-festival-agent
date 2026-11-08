import Button from "./Button.jsx";
export default function EmptyState({
  title = "아직 맞는 장면을 못 찾았어요.",
  children,
  onReset,
  resetLabel = "모든 축제 다시 보기",
}) {
  return (
    <div className="empty-search">
      <h3>{title}</h3>
      <p>{children}</p>
      {onReset && (
        <Button variant="white" onClick={onReset}>
          {resetLabel}
        </Button>
      )}
    </div>
  );
}
