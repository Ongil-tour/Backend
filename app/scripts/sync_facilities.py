"""
TourAPI 지역기반 목록 조회 -> contentId 순회 -> assemble_facility -> facilities upsert.
전국 시도(areaCode) x 검증된 콘텐츠타입(관광지/문화시설/숙박/음식점) 전체 페이지네이션.

실행:
  전국 전체: docker compose run --rm api python -m app.scripts.sync_facilities
  일부만(쿼터 아낄 때): docker compose run --rm api python -m app.scripts.sync_facilities --areas 1,31 --types 12,39
  이미 저장된 content_id는 기본적으로 skip(재실행해도 안전) - 강제 재조회는 --force

주의(API 쿼터): 목록조회 1콜 + 시설당 상세 3콜(detailCommon2/detailIntro2/detailWithTour2).
전국 전체를 한 번에 돌리면 대량 트래픽이 나가므로, --areas/--types로 나눠 여러 날에 걸쳐
돌리는 걸 권장한다. 이미 적재된 content_id는 기본 skip이라 하루치씩 나눠 돌려도 중복/누락 없이
이어서 진행된다.

카페/화장실/주차장은 TourAPI 표준 contentTypeId가 없어(무장애 여행정보 API 등 별도 소스 확인 필요)
이번 스케일업 범위에서 제외했다.
"""
import argparse
import time

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.facility import Facility
from app.services.facility_sync import assemble_facility
from app.services.tour_api import TourApiQuotaExceededError, get_area_based_list

# TourAPI 표준 시도 단위 areaCode 전체(17개)
AREA_NAMES = {
    "1": "서울", "2": "인천", "3": "대전", "4": "대구", "5": "광주", "6": "부산",
    "7": "울산", "8": "세종", "31": "경기", "32": "강원", "33": "충북", "34": "충남",
    "35": "경북", "36": "경남", "37": "전북", "38": "전남", "39": "제주",
}
ALL_AREA_CODES = list(AREA_NAMES)

# OPERATING_HOURS_FIELD_BY_TYPE(app/services/tour_api.py)에서 실제 검증된 콘텐츠타입만 사용.
CONTENT_TYPE_CATEGORY = {
    "12": "관광지",
    "14": "관광지",  # 문화시설 - 전용 카테고리 없어 관광지로 묶음
    "32": "숙소",
    "39": "식당",
}

NUM_OF_ROWS = 100            # 페이지당 목록 조회 건수
LIST_REQUEST_DELAY = 0.2     # 목록조회 페이지 간 딜레이(초)
DETAIL_REQUEST_DELAY = 0.1   # 시설 1건(상세 3콜) 처리 후 딜레이(초)


def upsert_facility(db: Session, row: dict) -> None:
    stmt = pg_insert(Facility).values(**row)
    update_cols = {k: v for k, v in row.items() if k != "content_id"}
    stmt = stmt.on_conflict_do_update(index_elements=["content_id"], set_=update_cols)
    db.execute(stmt)


def _existing_content_ids(db: Session) -> set[str]:
    return {row[0] for row in db.execute(select(Facility.content_id)).all()}


def _iter_area_content_items(area_code: str, content_type_id: str):
    """페이지네이션 끝까지 순회. 응답 건수가 NUM_OF_ROWS보다 적으면 마지막 페이지로 간주."""
    page_no = 1
    while True:
        items = get_area_based_list(content_type_id, area_code, num_of_rows=NUM_OF_ROWS, page_no=page_no)
        if not items:
            return
        yield from items
        if len(items) < NUM_OF_ROWS:
            return
        page_no += 1
        time.sleep(LIST_REQUEST_DELAY)


def sync(area_codes: list[str], content_types: dict[str, str], force: bool = False) -> None:
    db = SessionLocal()
    ok, failed, skipped = 0, 0, 0
    quota_exceeded = False
    try:
        already_synced = set() if force else _existing_content_ids(db)
        for area_code in area_codes:
            if quota_exceeded:
                break
            area_name = AREA_NAMES.get(area_code, area_code)
            for content_type_id, category in content_types.items():
                new_in_group = 0
                try:
                    for item in _iter_area_content_items(area_code, content_type_id):
                        content_id = item["contentid"]
                        if content_id in already_synced:
                            skipped += 1
                            continue
                        try:
                            row = assemble_facility(content_id, content_type_id, category=category)
                            upsert_facility(db, row)
                            db.commit()
                            already_synced.add(content_id)
                            ok += 1
                            new_in_group += 1
                            time.sleep(DETAIL_REQUEST_DELAY)
                        except TourApiQuotaExceededError:
                            raise
                        except Exception as e:
                            db.rollback()
                            failed += 1
                            print(f"  SKIP {content_id} ({item.get('title')}): {e}")
                except TourApiQuotaExceededError as e:
                    print(f"[{area_name}/{category}] 쿼터 초과로 중단: {e}")
                    quota_exceeded = True
                    break
                print(f"[{area_name}/{category}] 신규 {new_in_group}건 적재")
    finally:
        db.close()
    status = "쿼터 초과로 중단됨" if quota_exceeded else "완료"
    print(f"{status}: 성공 {ok}건, 스킵(기적재) {skipped}건, 실패 {failed}건")
    if quota_exceeded:
        print("이미 적재된 content_id는 다음 실행에서 자동 skip되니 그대로 재실행하면 이어서 진행된다.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TourAPI 시설 배치 적재")
    parser.add_argument("--areas", help="쉼표구분 areaCode 목록 (기본: 전국 17개)")
    parser.add_argument("--types", help="쉼표구분 contentTypeId 목록 (기본: 12,14,32,39)")
    parser.add_argument("--force", action="store_true", help="이미 저장된 content_id도 강제 재조회")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    areas = args.areas.split(",") if args.areas else ALL_AREA_CODES
    types = (
        {t: CONTENT_TYPE_CATEGORY[t] for t in args.types.split(",")}
        if args.types
        else CONTENT_TYPE_CATEGORY
    )
    sync(areas, types, force=args.force)
