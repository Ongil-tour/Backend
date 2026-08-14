import time
import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.facility import Facility


client = TestClient(app)


def get_favorite_lists():
    response = client.get("/favorites/lists")
    assert response.status_code == 200
    return response.json()


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

        return [str(facility.id) for facility in facilities]

    finally:
        db.close()


def delete_test_facilities(facility_ids: list[str]):
    """테스트가 끝난 후 생성한 시설을 삭제한다."""
    db = SessionLocal()

    try:
        uuid_ids = [uuid.UUID(facility_id) for facility_id in facility_ids]

        db.query(Facility).filter(
            Facility.id.in_(uuid_ids)
        ).delete(synchronize_session=False)

        db.commit()

    finally:
        db.close()


def create_favorite(list_id: str, facility_id: str, source: str = "internal"):
    return client.post(
        "/favorites",
        json={
            "list_id": list_id,
            "facility_id": facility_id,
            "source": source,
        },
    )


def delete_favorite(favorite_id: str):
    return client.delete(f"/favorites/{favorite_id}")


def test_get_favorite_lists():
    response = client.get("/favorites/lists")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3

    for item in data:
        assert "id" in item
        assert "list_type" in item
        assert "created_at" in item
        assert "favorite_count" in item
        assert isinstance(item["favorite_count"], int)


def test_get_empty_favorite_list_returns_empty_array():
    favorite_lists = get_favorite_lists()

    empty_list = next(
        (
            favorite_list
            for favorite_list in favorite_lists
            if favorite_list["favorite_count"] == 0
        ),
        None,
    )

    assert empty_list is not None

    response = client.get(
        f"/favorites/lists/{empty_list['id']}"
    )

    assert response.status_code == 200
    assert response.json() == []


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
    favorite_lists = get_favorite_lists()
    list_id = favorite_lists[0]["id"]

    response = create_favorite(
        list_id=list_id,
        facility_id=str(uuid.uuid4()),
    )

    assert response.status_code == 404


def test_duplicate_favorite_returns_409():
    favorite_lists = get_favorite_lists()
    list_id = favorite_lists[0]["id"]

    facility_ids = create_test_facilities(1)
    facility_id = facility_ids[0]
    favorite_id = None

    try:
        first_response = create_favorite(
            list_id=list_id,
            facility_id=facility_id,
        )

        assert first_response.status_code in (200, 201)

        favorite_id = first_response.json()["id"]

        duplicate_response = create_favorite(
            list_id=list_id,
            facility_id=facility_id,
        )

        assert duplicate_response.status_code == 409

    finally:
        if favorite_id is not None:
            delete_response = delete_favorite(favorite_id)
            assert delete_response.status_code in (200, 204)

        delete_test_facilities(facility_ids)


def test_favorites_are_sorted_by_latest():
    favorite_lists = get_favorite_lists()
    list_id = favorite_lists[0]["id"]

    facility_ids = create_test_facilities(2)
    created_favorite_ids = []

    try:
        first_response = create_favorite(
            list_id=list_id,
            facility_id=facility_ids[0],
        )

        assert first_response.status_code in (200, 201)
        created_favorite_ids.append(first_response.json()["id"])

        # created_at 값이 확실히 다르게 기록되도록 잠시 기다린다.
        time.sleep(0.1)

        second_response = create_favorite(
            list_id=list_id,
            facility_id=facility_ids[1],
        )

        assert second_response.status_code in (200, 201)
        created_favorite_ids.append(second_response.json()["id"])

        response = client.get(f"/favorites/lists/{list_id}")

        assert response.status_code == 200

        created_favorites = [
            favorite
            for favorite in response.json()
            if favorite["id"] in created_favorite_ids
        ]

        assert len(created_favorites) == 2

        created_at_values = [
            datetime.fromisoformat(
                favorite["created_at"].replace("Z", "+00:00")
            )
            for favorite in created_favorites
        ]

        assert created_at_values == sorted(
            created_at_values,
            reverse=True,
        )

        # 두 번째으로 저장한 즐겨찾기가 가장 먼저 나와야 한다.
        assert created_favorites[0]["id"] == created_favorite_ids[1]
        assert created_favorites[1]["id"] == created_favorite_ids[0]

    finally:
        for favorite_id in created_favorite_ids:
            delete_response = delete_favorite(favorite_id)
            assert delete_response.status_code in (200, 204)

        delete_test_facilities(facility_ids)


def test_create_favorite_with_non_uuid_internal_facility_id_returns_422():
    favorite_lists = get_favorite_lists()
    list_id = favorite_lists[0]["id"]

    response = create_favorite(
        list_id=list_id,
        facility_id="521460056",  # 카카오 place id 형식, internal 소스엔 UUID가 아니라 부적합
        source="internal",
    )

    assert response.status_code == 422


def test_create_kakao_favorite_skips_existence_check():
    """kakao 소스는 내부 DB에 없는 place id라도 재조회 없이 저장을 허용한다."""
    favorite_lists = get_favorite_lists()
    list_id = favorite_lists[0]["id"]
    facility_id = f"kakao-test-{uuid.uuid4().hex[:8]}"
    favorite_id = None

    try:
        response = create_favorite(
            list_id=list_id,
            facility_id=facility_id,
            source="kakao",
        )

        assert response.status_code == 201
        body = response.json()
        assert body["facility_id"] == facility_id
        assert body["source"] == "kakao"

        favorite_id = body["id"]

        status_response = client.get(
            f"/favorites/{facility_id}/status",
            params={"source": "kakao"},
        )
        assert status_response.status_code == 200
        assert status_response.json()["is_favorite"] is True

    finally:
        if favorite_id is not None:
            delete_response = delete_favorite(favorite_id)
            assert delete_response.status_code in (200, 204)


def test_favorite_count_matches_list_items():
    favorite_lists = get_favorite_lists()

    for favorite_list in favorite_lists:
        response = client.get(
            f"/favorites/lists/{favorite_list['id']}"
        )

        assert response.status_code == 200
        assert favorite_list["favorite_count"] == len(response.json())