"""Groq 연결 (docs/workflow.md). AI 채팅(agent/)과 태그 추출(batch/extract_tags.py)이 함께 사용.

- 모델 이름은 .env GROQ_MODEL (Tool 호출을 지원하는 모델). 2026-11-11 확인: openai/gpt-oss-120b
- 무료 플랜은 분당·하루 요청 수 제한이 있음 → 넘으면 AiError("AI_RATE_LIMITED")
"""

import json
import logging
from functools import lru_cache

import groq

from app.core.config import settings

logger = logging.getLogger(__name__)

TIMEOUT = 30.0


class AiError(Exception):
    def __init__(self, code: str, message: str = "AI 응답을 받지 못했어요. 잠시 후 다시 시도해 주세요."):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@lru_cache
def get_client() -> groq.Groq:
    if not settings.GROQ_API_KEY or not settings.GROQ_MODEL:
        raise AiError("AI_KEY_MISSING", "AI 설정(GROQ_API_KEY, GROQ_MODEL)이 비어 있어요.")
    return groq.Groq(api_key=settings.GROQ_API_KEY, timeout=TIMEOUT, max_retries=1)


def chat(
    messages: list[dict],
    *,
    tools: list[dict] | None = None,
    tool_choice: str | dict = "auto",
    json_mode: bool = False,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> dict:
    """Groq 호출 1번 → assistant 메시지 dict ({"role", "content", "tool_calls"?}). 실패하면 AiError"""
    params: dict = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        params["tools"] = tools
        params["tool_choice"] = tool_choice
    if json_mode:
        params["response_format"] = {"type": "json_object"}
    if settings.GROQ_MODEL.startswith("openai/gpt-oss"):
        # 추론 토큰도 분당 토큰 제한(무료 8,000)에 포함 → 낮게. 추론 내용은 응답에 넣지 않음
        params["reasoning_effort"] = "low"
        params["include_reasoning"] = False
    try:
        response = get_client().chat.completions.create(**params)
    except groq.RateLimitError as exc:
        logger.warning("Groq 사용량 제한: %s", exc)
        raise AiError("AI_RATE_LIMITED", "요청이 많아 AI가 잠시 쉬고 있어요. 1분 뒤 다시 시도해 주세요.") from exc
    except groq.APITimeoutError as exc:
        raise AiError("AI_TIMEOUT") from exc
    except groq.BadRequestError as exc:
        if recovered := _recover_tool_call(exc):
            return recovered
        logger.warning("Groq 오류: %s", exc)
        raise AiError("AI_ERROR") from exc
    except groq.GroqError as exc:
        logger.warning("Groq 오류: %s", exc)
        raise AiError("AI_ERROR") from exc

    if response.usage:
        logger.info("Groq 토큰: 입력 %s, 출력 %s", response.usage.prompt_tokens, response.usage.completion_tokens)
    message = response.choices[0].message
    result: dict = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        result["tool_calls"] = [
            {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
            for c in message.tool_calls
        ]
    return result


def _recover_tool_call(exc: groq.BadRequestError) -> dict | None:
    """모델이 목록에 없는 Tool 이름(예: 'json')으로 답하면 Groq가 400 tool_use_failed로 거절한다.
    거절된 원문(failed_generation)의 arguments가 최종 답변 모양이면 final_answer 호출로 바꿔 살린다."""
    body = exc.body if isinstance(exc.body, dict) else {}
    error = body.get("error", body)
    if not isinstance(error, dict) or error.get("code") != "tool_use_failed":
        return None
    try:
        generated = json.loads(error.get("failed_generation") or "")
    except (TypeError, json.JSONDecodeError):
        return None
    args = generated.get("arguments") if isinstance(generated, dict) else None
    if not isinstance(args, dict) or not isinstance(args.get("text"), str):
        return None
    logger.info("tool_use_failed 복구: %s → final_answer", generated.get("name"))
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"id": "recovered", "type": "function",
                        "function": {"name": "final_answer", "arguments": json.dumps(args, ensure_ascii=False)}}],
    }


def chat_json(messages: list[dict], **kwargs) -> dict:
    """JSON 객체로 답을 받을 때. 지시문에 'JSON' 단어와 형식 예시를 꼭 넣을 것"""
    content = chat(messages, json_mode=True, **kwargs)["content"]
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AiError("AI_BAD_RESPONSE", "AI 응답 형식이 올바르지 않아요.") from exc
    if not isinstance(data, dict):
        raise AiError("AI_BAD_RESPONSE", "AI 응답 형식이 올바르지 않아요.")
    return data
