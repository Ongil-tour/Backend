"""
TourAPI 지역기반 목록 조회 -> contentId 순회 -> assemble_facility -> facilities upsert.
시작 범위: 서울(areaCode=1) x 관광지(12)/음식점(39), 타입당 15건 (소량 검증용).
실행: docker compose run --rm api python -m app.scripts.sync_facilities
"""
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.facility import Facility
from app.services.facility_sync import assemble_facility
from app.services.tour_api import get_area_based_list

AREA_CODE = "1"
CONTENT_TYPE_CATEGORY = {
    "12": "관광지",
    "39": "식당",
}
NUM_OF_ROWS = 15


def upsert_facility(db: Session, row: dict) -> None:
    stmt = pg_insert(Facility).values(**row)
    update_cols = {k: v for k, v in row.items() if k != "content_id"}
    stmt = stmt.on_conflict_do_update(index_elements=["content_id"], set_=update_cols)
    db.execute(stmt)


def sync() -> None:
    db = SessionLocal()
    ok, failed = 0, 0
    try:
        for content_type_id, category in CONTENT_TYPE_CATEGORY.items():
            items = get_area_based_list(content_type_id, AREA_CODE, num_of_rows=NUM_OF_ROWS)
            print(f"[{category}] {len(items)}건 조회")
            for item in items:
                content_id = item["contentid"]
                try:
                    row = assemble_facility(content_id, content_type_id, category=category)
                    upsert_facility(db, row)
                    db.commit()
                    ok += 1
                except Exception as e:
                    db.rollback()
                    failed += 1
                    print(f"  SKIP {content_id} ({item.get('title')}): {e}")
    finally:
        db.close()
    print(f"완료: 성공 {ok}건, 실패 {failed}건")


if __name__ == "__main__":
    sync()
