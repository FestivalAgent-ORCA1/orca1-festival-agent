"""맞춤 추천 (docs/api-spec.md GET /api/festivals/recommended, docs/tool-spec.md 5번)

후보(오늘~60일) → score_festivals로 점수 → 상위 N개 → AI가 추천 이유 한 문장씩 (Groq 1번)
AI가 실패하면 점수 내역으로 만든 문장을 대신 씀 (홈 화면이 깨지지 않게)
"""

import json
import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent import prompts
from app.agent.client import AiError, chat_json
from app.core.constants import REGION_NAMES, TAGS
from app.core.errors import AppError
from app.models.festival import FestivalTag
from app.models.user import User, UserRegion, UserTag
from app.services import festival_service
from app.services.like_service import list_liked_ids
from app.tools.score_festivals import score_festivals

logger = logging.getLogger(__name__)

CANDIDATE_DAYS = 60
CANDIDATE_LIMIT = 200
TAG_NAMES = {t["code"]: t["name"] for t in TAGS}


def get_profile(db: Session, user: User | None) -> dict | None:
    """docs/tool-spec.md get_profile: {"age_group", "regions", "tags"}. 비로그인·첫 설정 전이면 None
    (BE2 user_service에 같은 함수가 생기면 그것으로 바꾼다)"""
    if user is None or not user.onboarded:
        return None
    return {
        "age_group": user.age_group,
        "regions": list(db.scalars(select(UserRegion.area_code).where(UserRegion.user_id == user.id))),
        "tags": list(db.scalars(select(UserTag.tag_code).where(UserTag.user_id == user.id))),
    }


def liked_tags_of(db: Session, liked_ids: list[str]) -> set[str] | None:
    """찜한 축제들의 태그 합집합. 찜이 없으면 None"""
    if not liked_ids:
        return None
    return set(db.scalars(select(FestivalTag.tag_code).where(FestivalTag.content_id.in_(liked_ids))))


def fallback_reason(festival: dict, profile: dict) -> str:
    """AI 없이 점수 내역으로 만드는 추천 이유"""
    parts = []
    matched = [TAG_NAMES[t] for t in festival.get("tags") or [] if t in set(profile.get("tags") or [])]
    if matched:
        parts.append(f"좋아하시는 {matched[0]} 축제예요")
    if festival.get("area_code") in set(profile.get("regions") or []):
        parts.append(f"선호 지역인 {REGION_NAMES.get(festival['area_code'], '')}에서 열려요")
    if festival.get("status") == "ongoing":
        parts.append("지금 진행 중이에요")
    elif festival["score_detail"]["date"] >= 12:
        parts.append("곧 시작해요")
    if not parts:
        return "가까운 날짜에 열리는 축제예요."
    return ", ".join(parts) + "."


def ai_reasons(festivals: list[dict], profile: dict) -> dict[str, str]:
    """Groq 1번으로 축제마다 추천 이유 한 문장. 실패하면 빈 dict"""
    rows = [
        {"content_id": f["content_id"], "title": f["title"], "area": f.get("area_name"),
         "dates": f"{f['start_date']}~{f['end_date']}", "tags": [TAG_NAMES.get(t, t) for t in f.get("tags") or []],
         "score_detail": f["score_detail"]}
        for f in festivals
    ]
    system = (
        "너는 축제 추천 이유를 쓰는 도우미야. " + prompts.profile_line(profile) + "\n"
        "각 축제마다 사용자에게 왜 맞는지 존댓말 한 문장(40자 이내)으로 써. 주어진 정보에 없는 내용은 쓰지 마.\n"
        'JSON으로만 답해: {"reasons": {"content_id": "이유", ...}}'
    )
    try:
        data = chat_json(
            [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(rows, ensure_ascii=False)}],
            temperature=0.5,
            max_tokens=1200,
        )
    except AiError as exc:
        logger.warning("추천 이유 AI 실패 → 기본 문장 사용: %s", exc.code)
        return {}
    reasons = data.get("reasons") if isinstance(data.get("reasons"), dict) else {}
    return {str(k): v.strip() for k, v in reasons.items() if isinstance(v, str) and v.strip()}


def recommend(db: Session, user: User, size: int = 10, *, use_ai: bool = True) -> list[dict]:
    profile = get_profile(db, user)
    if profile is None:
        raise AppError(400, "ONBOARDING_REQUIRED", "첫 설정(관심사·지역)을 먼저 완료해 주세요.")
    liked_ids = list_liked_ids(db, user)
    today = festival_service.today_kst()
    candidates = festival_service.list_festivals(
        db, start_date=today, end_date=today + timedelta(days=CANDIDATE_DAYS), size=CANDIDATE_LIMIT,
        liked_ids=frozenset(liked_ids),
    )["items"]
    scored = score_festivals(candidates, profile, liked_ids, today, liked_tags=liked_tags_of(db, liked_ids))["festivals"]
    top = scored[:size]
    reasons = ai_reasons(top, profile) if (use_ai and top) else {}
    return [
        {**{k: v for k, v in f.items() if k != "score_detail"}, "reason": reasons.get(f["content_id"]) or fallback_reason(f, profile)}
        for f in top
    ]
