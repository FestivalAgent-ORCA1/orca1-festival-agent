"""태그 추출 — 실제 AI를 부르지 않고 가짜 응답으로 확인"""

from app.agent.client import AiError
from app.batch import extract_tags as module
from app.models.festival import Festival, FestivalTag
from app.services.festival_service import today_kst


def add(db, content_id, title, tags=()):
    f = Festival(content_id=content_id, title=title, start_date=today_kst(), end_date=today_kst())
    f.tags = [FestivalTag(tag_code=t) for t in tags]
    db.add(f)
    db.commit()
    return f


def test_clean_tags():
    assert module.clean_tags(["Food", "food", "unknown", "music", "night", "art"]) == ["food", "music", "night"]
    assert module.clean_tags("food") == []


def test_extract_only_untagged(db, monkeypatch):
    add(db, "1", "김치 축제")
    add(db, "2", "재즈 페스티벌")
    add(db, "3", "이미 태그 있음", tags=["art"])
    sent = []

    def fake_chat_json(messages, **kwargs):
        sent.append(messages[1]["content"])
        return {"results": [
            {"content_id": "1", "tags": ["food", "nope"]},
            {"content_id": "2", "tags": ["bad"]},  # 유효한 태그 없음 → 저장 안 함
            {"content_id": "999", "tags": ["music"]},  # 요청하지 않은 축제 → 무시
        ]}

    monkeypatch.setattr(module, "chat_json", fake_chat_json)
    stats = module.extract_tags(db)
    assert stats == {"targets": 2, "tagged": 1, "skipped": 1, "ai_failed": 0}
    assert "이미 태그 있음" not in sent[0]
    assert db.get(Festival, "1").tag_codes == ["food"]
    assert db.get(Festival, "2").tag_codes == []
    assert db.get(Festival, "3").tag_codes == ["art"]


def test_stop_on_rate_limit(db, monkeypatch):
    for i in range(module.BATCH_SIZE + 1):
        add(db, str(i), f"축제{i}")
    calls = []

    def limited(messages, **kwargs):
        calls.append(1)
        raise AiError("AI_RATE_LIMITED")

    monkeypatch.setattr(module, "chat_json", limited)
    stats = module.extract_tags(db)
    assert len(calls) == 1  # 첫 묶음에서 멈춤
    assert stats["tagged"] == 0 and stats["ai_failed"] == module.BATCH_SIZE
