import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { repository } from "../api/repository.js";
import { useToast } from "../contexts/ToastContext.jsx";
import { buildHistory, lastItinerary } from "../lib/chat.js";
import { defaultScheduleTitle, toSchedulePayload } from "../lib/itinerary.js";
import ChatWindow from "../components/chat/ChatWindow.jsx";
import FestivalPreview from "../components/festival/FestivalPreview.jsx";
import SaveScheduleDialog from "../components/schedule/SaveScheduleDialog.jsx";

// 로그인하러 가는 동안 저장하려던 시간표를 잠깐 맡겨 둡니다.
const PENDING_KEY = "orca:pending-itinerary";

let nextId = 0;
const newId = () => `m${Date.now().toString(36)}-${(nextId += 1)}`;

const greeting = (festivalId) => ({
  id: "greeting",
  role: "assistant",
  local: true, // history로 보내지 않음
  blocks: [
    {
      type: "text",
      text: festivalId
        ? "이 축제로 하루 일정을 짜드릴게요. 언제 방문하실 예정인가요?"
        : "안녕하세요! 축제를 추천하고, 방문일에 맞춰 주변 장소와 함께 하루 일정을 짜드려요.",
    },
    {
      type: "quick_replies",
      options: festivalId
        ? [
            { label: "이번 토요일", message: "이번 토요일에 갈 거야. 일정 짜줘" },
            { label: "이번 일요일", message: "이번 일요일에 갈 거야. 일정 짜줘" },
          ]
        : [
            { label: "이번 주말 축제", message: "이번 주말에 갈 만한 축제 추천해줘" },
            { label: "야경 축제", message: "밤에 가기 좋은 축제 추천해줘" },
            { label: "일정 짜줘", message: "축제 일정 짜줘" },
          ],
    },
  ],
});

// StrictMode에서 초기값 함수가 두 번 불려도 같은 값을 읽도록, 지우기는 effect에서 합니다.
function readPendingItinerary() {
  try {
    const raw = sessionStorage.getItem(PENDING_KEY);
    const itinerary = raw ? JSON.parse(raw) : null;
    return Array.isArray(itinerary?.items) ? itinerary : null;
  } catch {
    return null;
  }
}

export default function ChatPage() {
  const [params] = useSearchParams();
  const festivalId = params.get("festival");
  const navigate = useNavigate();
  const notify = useToast();
  const [messages, setMessages] = useState(() => {
    const restored = repository.hasSession() ? readPendingItinerary() : null;
    return restored
      ? [
          greeting(festivalId),
          {
            id: newId(),
            role: "assistant",
            local: true,
            blocks: [
              { type: "text", text: "로그인 전에 만든 일정을 다시 가져왔어요. 저장 버튼을 눌러 주세요." },
              { type: "timeline", itinerary: restored, savable: true },
            ],
          },
        ]
      : [greeting(festivalId)];
  });
  const [pending, setPending] = useState(false);
  const [previewId, setPreviewId] = useState(null);
  const [saving, setSaving] = useState(null); // { messageId, index, itinerary }
  const controller = useRef(null);

  useEffect(() => {
    document.title = "AI 일정 플래너 — ORCA";
    if (repository.hasSession())
      try {
        sessionStorage.removeItem(PENDING_KEY);
      } catch {
        /* blocked storage */
      }
    return () => {
      controller.current?.abort();
      document.title = "ORCA — 주말의 입장권";
    };
  }, []);

  // conversation: 이번 요청 직전까지의 메시지 (보낼 user 메시지 포함)
  const request = useCallback(
    async (conversation, text) => {
      controller.current?.abort();
      const current = new AbortController();
      controller.current = current;
      setPending(true);
      const itinerary = lastItinerary(conversation);
      try {
        const reply = await repository.chat(
          {
            message: text,
            history: buildHistory(conversation.slice(0, -1)),
            context: {
              festival_content_id: festivalId || null,
              ...(itinerary ? { itinerary } : {}),
            },
          },
          current.signal,
        );
        if (current.signal.aborted) return;
        setMessages((list) => [
          ...list,
          reply.blocks.length
            ? { id: newId(), role: "assistant", blocks: reply.blocks }
            : {
                id: newId(),
                role: "assistant",
                blocks: [{ type: "text", text: "답변을 만들지 못했어요. 다르게 물어봐 주시겠어요?" }],
              },
        ]);
      } catch (error) {
        if (current.signal.aborted) return;
        setMessages((list) => [...list, { id: newId(), role: "error", error, retryText: text }]);
      } finally {
        if (controller.current === current) setPending(false);
      }
    },
    [festivalId],
  );

  const send = (text) => {
    if (pending) return;
    const conversation = [...messages, { id: newId(), role: "user", text }];
    setMessages(conversation);
    request(conversation, text);
  };

  const retry = () => {
    const last = messages.at(-1);
    if (last?.role !== "error" || pending) return;
    const conversation = messages.slice(0, -1);
    setMessages(conversation);
    request(conversation, last.retryText);
  };

  const askSave = (messageId, index, itinerary) => {
    if (!repository.hasSession()) {
      try {
        sessionStorage.setItem(PENDING_KEY, JSON.stringify(itinerary));
      } catch {
        /* 저장이 막혀 있으면 로그인 후 다시 만들어야 함 */
      }
      notify("일정을 저장하려면 로그인이 필요해요.");
      navigate(`/login?redirect=${encodeURIComponent("/chat")}`);
      return;
    }
    setSaving({ messageId, index, itinerary });
  };

  const save = async (title) => {
    const { messageId, index, itinerary } = saving;
    const created = await repository.createSchedule(toSchedulePayload(itinerary, title));
    setMessages((list) =>
      list.map((message) =>
        message.id === messageId
          ? { ...message, saved: { ...message.saved, [index]: created?.id } }
          : message,
      ),
    );
    setSaving(null);
    notify("내 일정에 저장했어요.");
  };

  const savingFestival = (() => {
    if (!saving) return null;
    for (const message of messages)
      for (const block of message.blocks || [])
        if (block.type === "festival_cards")
          for (const { festival } of block.items)
            if (festival.content_id === saving.itinerary.festival_content_id) return festival;
    const festivalItem = saving.itinerary.items.find((item) => item.category === "festival");
    return festivalItem ? { title: festivalItem.name } : null;
  })();

  return (
    <section className="wrap chat-page">
      <header className="chat-head">
        <div>
          <span className="eyebrow">ORCA AI PLANNER</span>
          <h1 className="display">어떤 하루를 보내고 싶어요?</h1>
          <p>축제를 고르고, 방문일만 알려 주시면 주변 장소까지 엮어 시간표를 만들어 드려요.</p>
        </div>
        <Link className="key white" to="/schedules">
          내 일정 보기
        </Link>
      </header>

      <ChatWindow
        messages={messages}
        pending={pending}
        onSend={send}
        onRetry={retry}
        onPreview={setPreviewId}
        onSave={askSave}
      />
      <p className="chat-foot">대화는 저장되지 않아요. 새로고침하면 사라지니 마음에 드는 일정은 저장해 두세요.</p>

      <FestivalPreview contentId={previewId} onNext={setPreviewId} onClose={() => setPreviewId(null)} />
      <SaveScheduleDialog
        open={Boolean(saving)}
        defaultTitle={saving ? defaultScheduleTitle(saving.itinerary, savingFestival) : ""}
        onClose={() => setSaving(null)}
        onSave={save}
      />
    </section>
  );
}
