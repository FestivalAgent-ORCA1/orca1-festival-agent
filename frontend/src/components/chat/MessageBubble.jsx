import { Link } from "react-router-dom";
import FestivalCard from "../festival/FestivalCard.jsx";
import ItineraryView from "../schedule/ItineraryView.jsx";
import Button from "../common/Button.jsx";
import QuickReply from "./QuickReply.jsx";

function Bubble({ role, children }) {
  return <p className={`bubble bubble--${role}`}>{children}</p>;
}

/**
 * 메시지 1개를 그립니다.
 * - user: 오른쪽 말풍선
 * - assistant: blocks를 위에서부터 순서대로 (모르는 type은 무시)
 * - error: 안내 말풍선 + 다시 보내기
 */
export default function MessageBubble({
  message,
  showQuickReplies = false,
  busy = false,
  onSend,
  onRetry,
  onPreview,
  onSave,
}) {
  if (message.role === "user")
    return (
      <li className="message message--user">
        <span className="sr-only">내 메시지</span>
        <Bubble role="user">{message.text}</Bubble>
      </li>
    );

  if (message.role === "error")
    return (
      <li className="message message--assistant">
        <span className="sr-only">오류</span>
        <div className="bubble bubble--error" role="alert">
          <p>{message.error?.message || "잠시 후 다시 시도해 주세요."}</p>
          {onRetry && (
            <Button variant="white" onClick={onRetry} disabled={busy}>
              다시 보내기
            </Button>
          )}
        </div>
      </li>
    );

  return (
    <li className="message message--assistant">
      <span className="sr-only">ORCA 답변</span>
      {message.blocks.map((block, index) => {
        const key = `${message.id}-${index}`;
        switch (block.type) {
          case "text":
            return (
              <Bubble key={key} role="assistant">
                {block.text}
              </Bubble>
            );
          case "festival_cards":
            return (
              <div key={key} className="chat-cards" aria-label="추천 축제">
                {block.items.map(({ festival, reason }) => (
                  <div className="chat-card" key={festival.content_id}>
                    <FestivalCard festival={festival} reason={reason} onPreview={onPreview} />
                  </div>
                ))}
              </div>
            );
          case "timeline": {
            const savedId = message.saved?.[index];
            return (
              <div key={key} className="chat-timeline">
                <ItineraryView
                  itinerary={block.itinerary}
                  actions={
                    block.savable &&
                    (savedId ? (
                      <Button as={Link} to={`/schedules/${savedId}`} variant="white">
                        저장됨 · 내 일정에서 보기
                      </Button>
                    ) : (
                      <Button variant="blue" onClick={() => onSave(message.id, index, block.itinerary)}>
                        일정 저장
                      </Button>
                    ))
                  }
                />
              </div>
            );
          }
          case "quick_replies":
            return showQuickReplies ? (
              <QuickReply key={key} options={block.options} onSelect={onSend} disabled={busy} />
            ) : null;
          default:
            return null;
        }
      })}
    </li>
  );
}
