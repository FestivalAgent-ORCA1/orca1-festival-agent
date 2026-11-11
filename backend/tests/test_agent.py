"""AI 채팅 — Groq는 가짜 응답으로 확인 (실제 호출 없음)"""

import json
from datetime import timedelta

import groq
import httpx

from app.agent import client as ai_client
from app.agent import loop
from app.agent.client import AiError
from app.agent.intent import classify_by_rules
from app.agent.prompts import date_line
from app.models.festival import Festival
from app.services.festival_service import today_kst
from app.tools.get_festival_detail import get_festival_detail
from app.tools.search_festivals import search_festivals


def add_festival(db, content_id="100", title="서울 빛축제", area="1", **kw):
    t = today_kst()
    f = Festival(content_id=content_id, title=title, start_date=t, end_date=t + timedelta(days=3), area_code=area, **kw)
    db.add(f)
    db.commit()
    return f


def tool_call(name, args, call_id="c1"):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"id": call_id, "type": "function",
                            "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}]}


def fake_ai(monkeypatch, replies):
    """replies를 순서대로 돌려주는 가짜 chat. 받은 messages를 기록"""
    seen = []

    def fake_chat(messages, **kwargs):
        seen.append([dict(m) for m in messages])
        return replies.pop(0)

    monkeypatch.setattr(loop, "chat", fake_chat)
    return seen


# ---- 규칙·지시문 ----


def test_intent_rules():
    assert classify_by_rules("빛초롱축제 일정 짜줘") == "itinerary"
    assert classify_by_rules("서울 코스 추천") == "itinerary"
    assert classify_by_rules("카페 추가해줘", {"itinerary": {"items": []}}) == "itinerary"
    assert classify_by_rules("카페 추가해줘") is None
    assert classify_by_rules("이번 주말 축제 추천해줘") is None


def test_date_line_weekend():
    from datetime import date
    assert "2026-11-11(수)" in date_line(date(2026, 11, 11))
    assert "2026-11-14(토)~2026-11-15(일)" in date_line(date(2026, 11, 11))


# ---- Tool ----


def test_search_festivals_tool(db):
    add_festival(db, "1", "서울 빛축제", "1")
    add_festival(db, "2", "부산 바다축제", "6")
    result = search_festivals(db, today_kst().isoformat(), area_codes=["1", "999"])
    assert result["ok"] and [f["content_id"] for f in result["festivals"]] == ["1"]
    assert isinstance(result["festivals"][0]["start_date"], str)  # JSON으로 바꿀 수 있어야 함
    assert search_festivals(db, "11월 14일")["error"]["code"] == "BAD_REQUEST"


def test_get_festival_detail_uses_fresh_db(db):
    from datetime import datetime
    add_festival(db, "1", overview="소개", detail_synced_at=datetime.now())

    def never(request):
        raise AssertionError("TourAPI를 부르면 안 됨")

    result = get_festival_detail(db, "1", client=httpx.Client(transport=httpx.MockTransport(never)))
    assert result["ok"] and result["festival"]["overview"] == "소개"
    assert get_festival_detail(db, "nope")["error"]["code"] == "FESTIVAL_NOT_FOUND"


# ---- 반복 처리 ----


def test_chat_search_then_final_answer(client, db, monkeypatch):
    add_festival(db, "100", "서울 빛축제")
    seen = fake_ai(monkeypatch, [
        tool_call("search_festivals", {"start_date": today_kst().isoformat(), "area_codes": ["1"]}),
        tool_call("final_answer", {
            "intent": "recommend", "text": "서울 빛축제를 추천해요.",
            "festival_ids": ["100", "999"],  # 999는 Tool 결과에 없음 → 카드에서 빠져야 함
            "reasons": {"100": "야경이 예뻐요."},
            "quick_replies": [{"label": "일정 짜줘", "message": "서울 빛축제로 일정 짜줘"}],
        }, "c2"),
    ])
    res = client.post("/api/agent/chat", json={"message": "서울 축제 추천해줘"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "recommend"
    assert [b["type"] for b in body["blocks"]] == ["text", "festival_cards", "quick_replies"]
    cards = body["blocks"][1]["items"]
    assert [c["festival"]["content_id"] for c in cards] == ["100"] and cards[0]["reason"] == "야경이 예뻐요."
    assert "overview" not in cards[0]["festival"]  # 카드는 FestivalSummary 모양
    # 두 번째 호출에 Tool 결과가 들어갔는지
    tool_msg = seen[1][-1]
    assert tool_msg["role"] == "tool" and "서울 빛축제" in tool_msg["content"]
    assert "2026" in seen[0][0]["content"] or "오늘은" in seen[0][0]["content"]  # 지시문에 오늘 날짜


def test_chat_plain_text_answer(client, monkeypatch):
    fake_ai(monkeypatch, [{"role": "assistant", "content": "안녕하세요! 축제를 찾아드려요."}])
    body = client.post("/api/agent/chat", json={"message": "안녕"}).json()
    assert body["blocks"] == [{"type": "text", "text": "안녕하세요! 축제를 찾아드려요."}]


def test_chat_too_many_rounds(client, monkeypatch):
    fake_ai(monkeypatch, [tool_call("search_festivals", {"start_date": "2026-11-11"}) for _ in range(loop.MAX_ROUNDS)])
    body = client.post("/api/agent/chat", json={"message": "축제"}).json()
    assert body["intent"] == "unknown" and body["blocks"][0]["text"] == loop.TOO_MANY_ROUNDS_TEXT


def test_chat_ai_error_is_502(client, monkeypatch):
    def fail(messages, **kwargs):
        raise AiError("AI_RATE_LIMITED", "요청이 많아요.")

    monkeypatch.setattr(loop, "chat", fail)
    res = client.post("/api/agent/chat", json={"message": "축제 추천"})
    assert res.status_code == 502 and res.json()["code"] == "EXTERNAL_API_ERROR"


def test_chat_validation(client):
    assert client.post("/api/agent/chat", json={"message": ""}).status_code == 422


def test_bad_tool_arguments_do_not_crash(db):
    state = loop.ChatState(db=db)
    assert loop.run_tool(state, "search_festivals", "not json")["error"]["code"] == "BAD_ARGUMENTS"
    assert loop.run_tool(state, "search_festivals", "{}")["error"]["code"] == "BAD_ARGUMENTS"  # start_date 없음
    assert loop.run_tool(state, "nope", "{}")["error"]["code"] == "UNKNOWN_TOOL"


# ---- Groq 400 tool_use_failed 복구 ----


def test_recover_tool_use_failed():
    generation = json.dumps({"name": "json", "arguments": {"intent": "smalltalk", "text": "안녕하세요"}}, ensure_ascii=False)
    response = httpx.Response(400, request=httpx.Request("POST", "https://api.groq.com"))
    exc = groq.BadRequestError("bad", response=response,
                               body={"error": {"code": "tool_use_failed", "failed_generation": generation}})
    recovered = ai_client._recover_tool_call(exc)
    assert recovered["tool_calls"][0]["function"]["name"] == "final_answer"
    assert json.loads(recovered["tool_calls"][0]["function"]["arguments"])["text"] == "안녕하세요"

    other = groq.BadRequestError("bad", response=response, body={"error": {"code": "other"}})
    assert ai_client._recover_tool_call(other) is None
