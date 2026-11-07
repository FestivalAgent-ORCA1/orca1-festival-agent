import Button from "./Button.jsx";
export default function ErrorState({ error, onRetry }) {
  return (
    <div className="error-state" role="alert">
      <h3>잠깐, 연결이 매끄럽지 않아요.</h3>
      <p>{error?.message || "정보를 불러오지 못했어요."}</p>
      {onRetry && (
        <Button variant="white" onClick={onRetry}>
          다시 시도
        </Button>
      )}
    </div>
  );
}
