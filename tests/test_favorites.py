import time
import uuid

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.facility import Facility
from app.models.favorite import Favorite


client = TestClient(app)


# =========================================================
# 공통 헬퍼 함수
# =========================================================


def get_favorite_lists() -> list[dict]:
    """현재 Mock 사용자의 즐겨찾기 목록을 조회한다."""
    response = client.get("/favorites/lists")

    assert response.status_code == 200, response.text

    return response.json()


def get_basic_favorite_list() -> dict:
    """테스트에 사용할 기본 즐겨찾기 목록 하나를 반환한다."""
    favorite_lists = get_favorite_lists()

    return next(
        favorite_list
        for favorite_list in favorite_lists
        if favorite_list["list_type"]
        in {
            "FREQUENT",
            "WISHLIST",
            "VISITED",
        }
    )


def create_test_facilities(count: int = 2) -> list[str]:
    """테스트에 사용할 시설을 DB에 직접 생성한다."""
    db = SessionLocal()

    try:
        facilities = []

        for index in range(count):
            unique_value = uuid.uuid4().hex

            facility = Facility(
                content_id=unique_value[:20],
                content_type_id="12",
                name=f"즐겨찾기 테스트 시설 {unique_value[:8]}",
                category="관광지",
                address="테스트 주소",
                lat=35.1796 + (index * 0.001),
                lng=129.0756 + (index * 0.001),
            )

            db.add(facility)
            facilities.append(facility)

        db.commit()

        for facility in facilities:
            db.refresh(facility)

        return [
            str(facility.id)
            for facility in facilities
        ]

    finally:
        db.close()


def delete_test_facilities(
    facility_ids: list[str],
) -> None:
    """테스트 시설과 연결된 즐겨찾기를 삭제한다."""
    if not facility_ids:
        return

    db = SessionLocal()

    try:
        uuid_ids = [
            uuid.UUID(facility_id)
            for facility_id in facility_ids
        ]

        (
            db.query(Favorite)
            .filter(
                Favorite.facility_id.in_(uuid_ids)
            )
            .delete(synchronize_session=False)
        )

        (
            db.query(Facility)
            .filter(
                Facility.id.in_(uuid_ids)
            )
            .delete(synchronize_session=False)
        )

        db.commit()

    finally:
        db.close()


def create_favorite(
    list_id: str,
    facility_id: str,
):
    """시설을 선택한 즐겨찾기 목록에 저장한다."""
    return client.post(
        "/favorites",
        json={
            "list_id": list_id,
            "facility_id": facility_id,
        },
    )


# =========================================================
# 기본 즐겨찾기 목록 테스트
# =========================================================


def test_get_favorite_lists():
    response = client.get("/favorites/lists")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 3

    list_types = {
        item["list_type"]
        for item in data
    }

    assert "FREQUENT" in list_types
    assert "WISHLIST" in list_types
    assert "VISITED" in list_types

    for item in data:
        assert "id" in item
        assert "list_type" in item
        assert "name" in item
        assert "created_at" in item
        assert "favorite_count" in item
        assert isinstance(
            item["favorite_count"],
            int,
        )


def test_get_nonexistent_favorite_list_returns_404():
    nonexistent_list_id = uuid.uuid4()

    response = client.get(
        f"/favorites/lists/{nonexistent_list_id}"
    )

    assert response.status_code == 404


def test_delete_nonexistent_favorite_returns_404():
    nonexistent_favorite_id = uuid.uuid4()

    response = client.delete(
        f"/favorites/{nonexistent_favorite_id}"
    )

    assert response.status_code == 404


def test_create_favorite_with_nonexistent_facility_returns_404():
    favorite_list = get_basic_favorite_list()
    list_id = favorite_list["id"]

    response = create_favorite(
        list_id=list_id,
        facility_id=str(uuid.uuid4()),
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "시설을 찾을 수 없습니다."
    )


def test_duplicate_favorite_returns_409():
    favorite_list = get_basic_favorite_list()
    list_id = favorite_list["id"]

    facility_ids = create_test_facilities(1)
    facility_id = facility_ids[0]

    try:
        first_response = create_favorite(
            list_id=list_id,
            facility_id=facility_id,
        )

        assert first_response.status_code == 201
        assert (
            first_response.json()["list_id"]
            == list_id
        )
        assert (
            first_response.json()["facility_id"]
            == facility_id
        )

        second_response = create_favorite(
            list_id=list_id,
            facility_id=facility_id,
        )

        assert second_response.status_code == 409
        assert (
            second_response.json()["detail"]
            == "해당 시설은 이미 이 목록에 저장되어 있습니다."
        )

    finally:
        delete_test_facilities(facility_ids)


def test_favorites_are_sorted_by_latest():
    favorite_list = get_basic_favorite_list()
    list_id = favorite_list["id"]

    facility_ids = create_test_facilities(2)

    first_facility_id = facility_ids[0]
    second_facility_id = facility_ids[1]

    try:
        first_response = create_favorite(
            list_id=list_id,
            facility_id=first_facility_id,
        )

        assert first_response.status_code == 201
        first_favorite = first_response.json()

        time.sleep(0.2)

        second_response = create_favorite(
            list_id=list_id,
            facility_id=second_facility_id,
        )

        assert second_response.status_code == 201
        second_favorite = second_response.json()

        list_response = client.get(
            f"/favorites/lists/{list_id}"
        )

        assert list_response.status_code == 200

        favorites = list_response.json()

        test_favorites = [
            favorite
            for favorite in favorites
            if favorite["facility_id"]
            in facility_ids
        ]

        assert len(test_favorites) == 2

        assert (
            test_favorites[0]["id"]
            == second_favorite["id"]
        )
        assert (
            test_favorites[0]["facility_id"]
            == second_facility_id
        )

        assert (
            test_favorites[1]["id"]
            == first_favorite["id"]
        )
        assert (
            test_favorites[1]["facility_id"]
            == first_facility_id
        )

        assert (
            test_favorites[0]["created_at"]
            >= test_favorites[1]["created_at"]
        )

    finally:
        delete_test_facilities(facility_ids)


def test_favorite_count_increases_after_adding_items():
    favorite_list = get_basic_favorite_list()
    list_id = favorite_list["id"]

    initial_count = favorite_list["favorite_count"]

    facility_ids = create_test_facilities(2)

    try:
        for facility_id in facility_ids:
            response = create_favorite(
                list_id=list_id,
                facility_id=facility_id,
            )

            assert response.status_code == 201

        favorite_lists = get_favorite_lists()

        updated_list = next(
            item
            for item in favorite_lists
            if item["id"] == list_id
        )

        assert (
            updated_list["favorite_count"]
            == initial_count + 2
        )

    finally:
        delete_test_facilities(facility_ids)


def test_favorite_status_after_adding_facility():
    favorite_list = get_basic_favorite_list()
    list_id = favorite_list["id"]

    facility_ids = create_test_facilities(1)
    facility_id = facility_ids[0]

    try:
        create_response = create_favorite(
            list_id=list_id,
            facility_id=facility_id,
        )

        assert create_response.status_code == 201

        status_response = client.get(
            "/favorites/status",
            params={
                "facility_id": facility_id,
            },
        )

        assert status_response.status_code == 200

        data = status_response.json()

        assert data["is_favorite"] is True
        assert list_id in data["favorite_list_ids"]

    finally:
        delete_test_facilities(facility_ids)