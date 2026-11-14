"""축제 목록 갱신 (docs/workflow.md 자동 실행 작업, 담당 BE1)

오늘~90일 뒤 축제를 searchFestival2로 받아 festivals에 저장·갱신하고,
새 축제이거나 modifiedtime이 바뀐 축제만 상세(detailCommon2)·소개(detailIntro2)를 다시 받는다.

직접 실행 (backend/에서, 공용 DB에 쓰므로 BE1만):
    python -m app.batch.sync_festivals             # 전체
    python -m app.batch.sync_festivals --max-detail 20   # 상세는 20개만 (호출 수 아끼기)
"""

import argparse
import logging
from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.festival import Festival
from app.services.festival_service import KST, today_kst
from app.tools import tourapi_client as tour

logger = logging.getLogger(__name__)

DAYS_AHEAD = 90
PAGE_SIZE = 100


def fetch_festival_list(client: httpx.Client, days: int = DAYS_AHEAD) -> list[dict]:
    today = today_kst()
    params = {
        "eventStartDate": today.strftime("%Y%m%d"),
        "eventEndDate": (today + timedelta(days=days)).strftime("%Y%m%d"),
        "arrange": "C",  # 수정일 순
        "numOfRows": PAGE_SIZE,
    }
    items: list[dict] = []
    page = 1
    while True:
        result = tour.call("searchFestival2", {**params, "pageNo": page}, client=client)
        items.extend(result["items"])
        if not result["items"] or len(items) >= result["total"]:
            return items
        page += 1


def apply_summary(festival: Festival, item: dict) -> None:
    address = " ".join(filter(None, [tour.text(item.get("addr1")), tour.text(item.get("addr2"))]))
    festival.title = tour.text(item.get("title")) or festival.title
    festival.start_date = tour.parse_date(item.get("eventstartdate")) or festival.start_date
    festival.end_date = tour.parse_date(item.get("eventenddate")) or festival.end_date
    festival.area_code = tour.area_code_of(item)
    festival.sigungu_code = tour.text(item.get("sigungucode"))
    festival.address = address[:300] or None
    festival.lng = tour.to_float(item.get("mapx"))
    festival.lat = tour.to_float(item.get("mapy"))
    festival.image_url = tour.text(item.get("firstimage"))
    festival.thumbnail_url = tour.text(item.get("firstimage2"))
    festival.tel = (tour.clean_html(item.get("tel")) or "")[:100] or None


def apply_detail(client: httpx.Client, festival: Festival) -> None:
    common = tour.call("detailCommon2", {"contentId": festival.content_id}, client=client)["items"]
    intro = tour.call(
        "detailIntro2", {"contentId": festival.content_id, "contentTypeId": 15}, client=client
    )["items"]
    if common:
        overview = tour.clean_html(common[0].get("overview"))
        if festival.overview is not None and overview != festival.overview:
            festival.tags.clear()  # 소개글이 바뀌면 extract_tags가 다시 붙이도록 기존 태그 삭제
        festival.overview = overview
        festival.homepage = (tour.extract_url(common[0].get("homepage")) or "")[:1000] or None
    if intro:
        festival.place = (tour.clean_html(intro[0].get("eventplace")) or "")[:300] or None
        festival.playtime = (tour.clean_html(intro[0].get("playtime")) or "")[:300] or None
        festival.fee = (tour.clean_html(intro[0].get("usetimefestival")) or "")[:500] or None
    festival.detail_synced_at = datetime.now(KST).replace(tzinfo=None)


def sync_festivals(db: Session, *, client: httpx.Client | None = None, max_detail: int | None = None) -> dict:
    """반환: {"fetched", "created", "updated", "detail_synced", "detail_failed"}"""
    owns_client = client is None
    client = client or httpx.Client(timeout=tour.TIMEOUT)
    stats = {"fetched": 0, "created": 0, "updated": 0, "detail_synced": 0, "detail_failed": 0}
    try:
        items = fetch_festival_list(client)
        stats["fetched"] = len(items)
        for item in items:
            content_id = tour.text(item.get("contentid"))
            start = tour.parse_date(item.get("eventstartdate"))
            end = tour.parse_date(item.get("eventenddate"))
            if not content_id or not start or not end or not tour.text(item.get("title")):
                continue  # 필수 값이 없는 데이터는 건너뜀
            festival = db.get(Festival, content_id)
            modified = tour.parse_datetime(item.get("modifiedtime"))
            if festival is None:
                festival = Festival(content_id=content_id)
                db.add(festival)
                stats["created"] += 1
            else:
                stats["updated"] += 1
            changed = festival.tourapi_modified_at != modified or festival.detail_synced_at is None
            apply_summary(festival, item)
            festival.tourapi_modified_at = modified

            if changed and (max_detail is None or stats["detail_synced"] < max_detail):
                try:
                    apply_detail(client, festival)
                    stats["detail_synced"] += 1
                except tour.TourApiError as exc:
                    stats["detail_failed"] += 1
                    logger.warning("상세 실패 %s: %s", content_id, exc)
            db.commit()  # 한 건씩 저장 (중간에 실패해도 앞부분은 남음)
        return stats
    finally:
        if owns_client:
            client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="TourAPI 축제 동기화")
    parser.add_argument("--max-detail", type=int, default=None, help="상세를 받을 최대 축제 수")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with SessionLocal() as db:
        print(sync_festivals(db, max_detail=args.max_detail))


if __name__ == "__main__":
    main()
