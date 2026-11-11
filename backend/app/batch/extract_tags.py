"""축제 태그 붙이기 (docs/workflow.md 자동 실행 작업, docs/tags.md 1장, 담당 BE1)

태그가 없는 축제만 골라 제목·장소·소개글을 AI(Groq)에 보내고 태그 1~3개를 받아 festival_tags에 저장한다.
- 소개글이 바뀐 축제는 sync_festivals가 기존 태그를 지우므로 자동으로 다시 대상이 된다
- tags.md 목록에 없는 코드는 버림. 유효한 태그가 하나도 없으면 저장하지 않음 (다음 실행 때 다시 시도)
- Groq 무료 사용량을 아끼려고 축제 BATCH_SIZE개를 한 번에 보냄

직접 실행 (backend/에서, 공용 DB에 쓰므로 BE1만):
    python -m app.batch.extract_tags              # 태그 없는 축제 전부
    python -m app.batch.extract_tags --limit 20   # 20개만
"""

import argparse
import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.client import AiError, chat_json
from app.core.constants import TAG_CODES, TAGS
from app.core.db import SessionLocal
from app.models.festival import Festival, FestivalTag

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
OVERVIEW_CHARS = 400  # 토큰 절약
MAX_TAGS = 3

SYSTEM_PROMPT = (
    "너는 한국 축제 분류기야. 각 축제에 아래 태그 중 가장 잘 맞는 것을 1~3개 골라.\n"
    "태그 목록 (코드: 이름 - 이런 축제):\n"
    + "\n".join(f"- {t['code']}: {t['name']}" for t in TAGS)
    + "\n\n규칙: 목록에 있는 코드만 사용. 확실한 것만, 많아도 3개.\n"
    '반드시 JSON으로만 답해: {"results": [{"content_id": "...", "tags": ["code", ...]}, ...]}'
)


def targets(db: Session, limit: int | None = None) -> list[Festival]:
    """태그가 하나도 없는 축제 (종료일이 가까운 것부터)"""
    stmt = (
        select(Festival)
        .where(~select(FestivalTag.content_id).where(FestivalTag.content_id == Festival.content_id).exists())
        .order_by(Festival.end_date, Festival.content_id)
    )
    if limit:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def _festival_input(f: Festival) -> dict:
    return {
        "content_id": f.content_id,
        "title": f.title,
        "place": f.place,
        "overview": (f.overview or "")[:OVERVIEW_CHARS] or None,
    }


def clean_tags(raw) -> list[str]:
    """목록에 없는 코드·중복 제거, 최대 3개"""
    if not isinstance(raw, list):
        return []
    result: list[str] = []
    for code in raw:
        code = str(code).strip().lower()
        if code in TAG_CODES and code not in result:
            result.append(code)
    return result[:MAX_TAGS]


def ask_tags(festivals: list[Festival]) -> dict[str, list[str]]:
    """AI 호출 1번 → {content_id: [태그]}. 실패하면 AiError"""
    data = chat_json(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps([_festival_input(f) for f in festivals], ensure_ascii=False)},
        ],
        temperature=0,
        max_tokens=2000,
    )
    wanted = {f.content_id for f in festivals}
    out: dict[str, list[str]] = {}
    for row in data.get("results") or []:
        if isinstance(row, dict) and str(row.get("content_id")) in wanted:
            out[str(row["content_id"])] = clean_tags(row.get("tags"))
    return out


def extract_tags(db: Session, *, limit: int | None = None) -> dict:
    """반환: {"targets", "tagged", "skipped", "ai_failed"}. 사용량 제한에 걸리면 거기서 멈춤"""
    festivals = targets(db, limit)
    stats = {"targets": len(festivals), "tagged": 0, "skipped": 0, "ai_failed": 0}
    for start in range(0, len(festivals), BATCH_SIZE):
        chunk = festivals[start : start + BATCH_SIZE]
        try:
            result = ask_tags(chunk)
        except AiError as exc:
            stats["ai_failed"] += len(chunk)
            logger.warning("태그 추출 실패 (%d개): %s", len(chunk), exc)
            if exc.code in ("AI_RATE_LIMITED", "AI_KEY_MISSING"):
                break  # 다음 실행 때 이어서
            continue
        for festival in chunk:
            tags = result.get(festival.content_id) or []
            if not tags:
                stats["skipped"] += 1
                continue
            festival.tags = [FestivalTag(tag_code=code) for code in tags]
            stats["tagged"] += 1
        db.commit()  # 묶음마다 저장
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="축제 태그 추출 (Groq)")
    parser.add_argument("--limit", type=int, default=None, help="처리할 최대 축제 수")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with SessionLocal() as db:
        print(extract_tags(db, limit=args.limit))


if __name__ == "__main__":
    main()
