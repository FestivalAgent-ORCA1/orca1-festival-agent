import { ApiError } from "./client.js";
import { normalizeBlocks } from "../lib/chat.js";

// agent-response-format.md: 채팅 요청 타임아웃 30초
export const CHAT_TIMEOUT_MS = 30000;

export function createAgentApi(request, { timeoutMs = CHAT_TIMEOUT_MS } = {}) {
  return {
    async chat({ message, history = [], context = {} }, signal) {
      const controller = new AbortController();
      const abort = () => controller.abort(signal.reason);
      if (signal?.aborted) abort();
      else signal?.addEventListener("abort", abort, { once: true });
      let timedOut = false;
      const timer = setTimeout(() => {
        timedOut = true;
        controller.abort();
      }, timeoutMs);
      try {
        const result = await request("/api/agent/chat", {
          method: "POST",
          body: { message, history, context },
          signal: controller.signal,
        });
        return {
          intent: result?.intent || "unknown",
          blocks: normalizeBlocks(result?.blocks),
        };
      } catch (error) {
        if (timedOut && !signal?.aborted)
          throw new ApiError(
            0,
            "TIMEOUT",
            "답변이 늦어지고 있어요. 잠시 후 다시 보내 주세요.",
          );
        throw error;
      } finally {
        clearTimeout(timer);
        signal?.removeEventListener("abort", abort);
      }
    },
  };
}
