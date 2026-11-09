import { useEffect, useRef, useState } from "react";
import { MESSAGE_MAX } from "../../lib/chat.js";
import Button from "../common/Button.jsx";
import Icon from "../common/Icon.jsx";
import MessageBubble from "./MessageBubble.jsx";
import "../../styles/planner.css";

/**
 * 말풍선 목록 + 답변 기다리는 중 표시 + 입력창.
 * 대화 상태와 요청은 ChatPage가 관리하고, 여기서는 그리기와 입력만 담당합니다.
 */
export default function ChatWindow({ messages, pending, onSend, onRetry, onPreview, onSave }) {
  const [draft, setDraft] = useState("");
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const lastId = messages.at(-1)?.id;

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages.length, pending]);

  const send = (text) => {
    const value = text.trim();
    if (!value || pending) return;
    onSend(value.slice(0, MESSAGE_MAX));
    setDraft("");
    inputRef.current?.focus();
  };

  return (
    <div className="chat-window">
      <ol className="message-list" aria-live="polite" aria-busy={pending}>
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            // 새 메시지를 보내면 이전 선택지는 숨깁니다.
            showQuickReplies={message.id === lastId && !pending}
            busy={pending}
            onSend={send}
            onRetry={message.id === lastId ? onRetry : undefined}
            onPreview={onPreview}
            onSave={onSave}
          />
        ))}
        {pending && (
          <li className="message message--assistant">
            <p className="bubble bubble--assistant bubble--typing" role="status">
              <span className="typing-dots" aria-hidden="true">
                <i />
                <i />
                <i />
              </span>
              답변 작성 중...
            </p>
          </li>
        )}
      </ol>
      <div ref={endRef} className="chat-end" />

      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault();
          send(draft);
        }}
      >
        <label htmlFor="chat-input" className="sr-only">
          메시지 입력
        </label>
        <textarea
          id="chat-input"
          ref={inputRef}
          rows={1}
          value={draft}
          maxLength={MESSAGE_MAX}
          placeholder="예) 이번 주말 서울 근처 축제 추천해줘"
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            // Enter로 보내기, Shift+Enter로 줄바꿈 (한글 조합 중에는 보내지 않음)
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              send(draft);
            }
          }}
        />
        {draft.length > MESSAGE_MAX - 100 && (
          <span className="composer-count">
            {draft.length}/{MESSAGE_MAX}
          </span>
        )}
        <Button type="submit" variant="blue" className="composer-send" disabled={pending || !draft.trim()} aria-label="보내기">
          <Icon name="arrow" />
        </Button>
      </form>
    </div>
  );
}
