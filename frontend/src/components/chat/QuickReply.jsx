// 선택지 버튼: 누르면 message를 사용자가 입력한 것처럼 보냅니다.
export default function QuickReply({ options = [], onSelect, disabled = false }) {
  if (!options.length) return null;
  return (
    <div className="quick-replies" role="group" aria-label="추천 답변">
      {options.map((option) => (
        <button
          key={`${option.label}-${option.message}`}
          type="button"
          className="mood quick-reply"
          disabled={disabled}
          onClick={() => onSelect(option.message)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
