// AI 채팅 응답 처리용 순수 함수 (FE2). 형식은 docs/agent-response-format.md를 따릅니다.

export const MESSAGE_MAX = 500;
export const HISTORY_MAX = 10;
const CARD_MAX = 5;
const QUICK_REPLY_MAX = 4;

const isText = (value) => typeof value === "string" && value.trim() !== "";

// 모르는 type, 모양이 맞지 않는 블록은 오류 없이 버립니다.
export function normalizeBlocks(blocks) {
  if (!Array.isArray(blocks)) return [];
  const result = [];
  for (const block of blocks) {
    if (!block || typeof block !== "object") continue;
    if (block.type === "text" && isText(block.text)) {
      result.push({ type: "text", text: block.text });
    } else if (block.type === "festival_cards" && Array.isArray(block.items)) {
      const items = block.items
        .filter((item) => item?.festival?.content_id && item.festival.title)
        .slice(0, CARD_MAX)
        .map((item) => ({
          festival: item.festival,
          reason: isText(item.reason) ? item.reason : null,
        }));
      if (items.length) result.push({ type: "festival_cards", items });
    } else if (
      block.type === "timeline" &&
      block.itinerary &&
      Array.isArray(block.itinerary.items)
    ) {
      result.push({
        type: "timeline",
        itinerary: {
          ...block.itinerary,
          warnings: Array.isArray(block.itinerary.warnings)
            ? block.itinerary.warnings
            : [],
        },
        savable: block.savable === true,
      });
    } else if (block.type === "quick_replies" && Array.isArray(block.options)) {
      const options = block.options
        .filter((option) => isText(option?.label) && isText(option?.message))
        .slice(0, QUICK_REPLY_MAX)
        .map(({ label, message }) => ({
          label,
          message: message.slice(0, MESSAGE_MAX),
        }));
      if (options.length) result.push({ type: "quick_replies", options });
    }
  }
  // 선택지는 항상 마지막 블록 하나만 사용합니다.
  const replies = result.filter((block) => block.type === "quick_replies");
  const others = result.filter((block) => block.type !== "quick_replies");
  return replies.length ? [...others, replies.at(-1)] : others;
}

export const blocksText = (blocks) =>
  (blocks || [])
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("\n");

// 화면 메시지 → 요청의 history (최근 10개, 글만)
export function buildHistory(messages) {
  return messages
    .flatMap((message) => {
      if (message.local) return [];
      if (message.role === "user") return [{ role: "user", text: message.text }];
      if (message.role === "assistant") {
        const text = blocksText(message.blocks);
        return text ? [{ role: "assistant", text }] : [];
      }
      return [];
    })
    .slice(-HISTORY_MAX);
}

// 일정 수정 요청용: 화면에 있는 마지막 시간표
export function lastItinerary(messages) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const blocks = messages[i].blocks || [];
    for (let j = blocks.length - 1; j >= 0; j -= 1)
      if (blocks[j].type === "timeline") return blocks[j].itinerary;
  }
  return null;
}
