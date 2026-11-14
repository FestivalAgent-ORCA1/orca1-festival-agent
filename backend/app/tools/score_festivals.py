"""Tool: score_festivals — 추천 점수 (계산만, docs/tool-spec.md 5번)

100점 만점 (초안 — 테스트하며 조정)
| 항목       | 배점 | 계산 |
| 관심사 일치 | 40  | 사용자 태그와 겹치는 축제 태그 수 ÷ 축제 태그 수 × 40 |
| 선호 지역   | 25  | 선호 지역이면 25, 선호 지역이 없으면(전국) 모두 12 |
| 찜 유사도   | 20  | 찜한 축제들의 태그와 겹치는 정도 (찜이 없으면 모두 10) |
| 날짜       | 15  | 진행 중 15, 7일 이내 시작 12, 30일 이내 8, 그 이후 3 |
이미 찜한 축제, 종료된 축제는 제외. 추천 이유 문장은 여기서 만들지 않음.
"""

from datetime import date


def _as_date(value) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def date_score(start: date, end: date, today: date) -> int:
    if start <= today <= end:
        return 15
    days = (start - today).days
    if days <= 7:
        return 12
    if days <= 30:
        return 8
    return 3


def score_one(festival: dict, profile: dict, liked_tags: set[str] | None, today: date) -> dict:
    tags = set(festival.get("tags") or [])
    user_tags = set(profile.get("tags") or [])
    regions = set(profile.get("regions") or [])

    tag = round(len(tags & user_tags) / len(tags) * 40) if tags else 0
    region = (25 if festival.get("area_code") in regions else 0) if regions else 12
    if liked_tags is None:
        liked = 10
    else:
        liked = round(len(tags & liked_tags) / len(tags) * 20) if tags else 0
    when = date_score(_as_date(festival["start_date"]), _as_date(festival["end_date"]), today)
    detail = {"tag": tag, "region": region, "liked": liked, "date": when}
    return {**festival, "score": sum(detail.values()), "score_detail": detail}


def score_festivals(
    festivals: list[dict],
    profile: dict | None,
    liked_ids: list[str] | set[str] | frozenset[str] = (),
    today: str | date | None = None,
    *,
    liked_tags: set[str] | None = None,
) -> dict:
    """{"ok": True, "festivals": [{**FestivalSummary, "score", "score_detail"}]} 점수 높은 순

    liked_tags: 찜한 축제들의 태그 합집합 (서비스가 DB에서 구해서 넘김). 찜이 없으면 None
    """
    today = _as_date(today) if today else date.today()
    profile = profile or {}
    liked = set(liked_ids)
    candidates = [
        f for f in festivals
        if f["content_id"] not in liked and _as_date(f["end_date"]) >= today
    ]
    scored = [score_one(f, profile, liked_tags if liked else None, today) for f in candidates]
    scored.sort(key=lambda f: (-f["score"], str(f["start_date"]), f["content_id"]))
    return {"ok": True, "festivals": scored}
