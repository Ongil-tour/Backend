import time
import uuid
<<<<<<< HEAD
=======
from datetime import datetime
>>>>>>> upstream/main

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.facility import Facility
<<<<<<< HEAD
from app.models.favorite import Favorite, FavoriteList
=======
>>>>>>> upstream/main


client = TestClient(app)


<<<<<<< HEAD
# =========================================================
# 공통 헬퍼 함수
# =========================================================


def get_favorite_lists() -> list[dict]:
    """현재 Mock 사용자의 즐겨찾기 목록을 조회한다."""
    response = client.get("/favorites/lists")

    assert response.status_code == 200, response.text

=======
def get_favorite_lists():
    response = client.get("/favorites/lists")
    assert response.status_code == 200
>>>>>>> upstream/main
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

<<<<<<< HEAD
        return [
            str(facility.id)
            for facility in facilities
        ]
=======
        return [str(facility.id) for facility in facilities]
>>>>>>> upstream/main

    finally:
        db.close()


<<<<<<< HEAD
def delete_test_facilities(
    facility_ids: list[str],
) -> None:
    """테스트 중 생성한 시설을 삭제한다."""
    if not facility_ids:
        return

    db = SessionLocal()

    try:
        uuid_ids = [
            uuid.UUID(facility_id)
            for facility_id in facility_ids
        ]

        # 시설을 삭제하기 전에 연결된 즐겨찾기 항목을 먼저 삭제한다.
        (
            db.query(Favorite)
            .filter(Favorite.facility_id.in_(uuid_ids))
            .delete(synchronize_session=False)
        )

        (
            db.query(Facility)
            .filter(Facility.id.in_(uuid_ids))
            .delete(synchronize_session=False)
        )
=======
def delete_test_facilities(facility_ids: list[str]):
    """테스트가 끝난 후 생성한 시설을 삭제한다."""
    db = SessionLocal()

    try:
        uuid_ids = [uuid.UUID(facility_id) for facility_id in facility_ids]

        db.query(Facility).filter(
            Facility.id.in_(uuid_ids)
        ).delete(synchronize_session=False)
>>>>>>> upstream/main

        db.commit()

    finally:
        db.close()


<<<<<<< HEAD
def create_test_custom_list(
    prefix: str = "테스트 목록",
) -> dict:
    """테스트마다 고유한 사용자 지정 목록을 생성한다."""
    unique_name = f"{prefix}-{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/favorites/lists",
        json={
            "name": unique_name,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def delete_test_custom_list(
    list_id: str,
) -> None:
    """테스트에서 생성한 사용자 지정 목록을 삭제한다."""
    response = client.delete(
        f"/favorites/lists/{list_id}"
    )

    assert response.status_code in (204, 404), response.text


def create_favorite(
    list_id: str,
    facility_id: str,
):
    """전달받은 목록에 시설을 즐겨찾기로 저장한다."""
=======
def create_favorite(list_id: str, facility_id: str):
>>>>>>> upstream/main
    return client.post(
        "/favorites",
        json={
            "list_id": list_id,
            "facility_id": facility_id,
        },
    )


<<<<<<< HEAD
def delete_favorite(
    favorite_id: str,
):
    """즐겨찾기 항목을 삭제한다."""
    return client.delete(
        f"/favorites/{favorite_id}"
    )


# =========================================================
# 즐겨찾기 목록 조회 테스트
# =========================================================
=======
def delete_favorite(favorite_id: str):
    return client.delete(f"/favorites/{favorite_id}")
>>>>>>> upstream/main


def test_get_favorite_lists():
    response = client.get("/favorites/lists")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
<<<<<<< HEAD
    assert len(data) >= 3

    list_types = {
        item["list_type"]
        for item in data
    }

    assert "FREQUENT" in list_types
    assert "VISITED" in list_types
    assert "WISHLIST" in list_types
=======
    assert len(data) == 3
>>>>>>> upstream/main

    for item in data:
        assert "id" in item
        assert "list_type" in item
<<<<<<< HEAD
        assert "name" in item
        assert "created_at" in item
        assert "favorite_count" in item
        assert isinstance(
            item["favorite_count"],
            int,
        )


def test_get_empty_favorite_list_returns_empty_array():
    custom_list = create_test_custom_list(
        prefix="빈 목록 조회 테스트"
    )
    list_id = custom_list["id"]

    try:
        response = client.get(
            f"/favorites/lists/{list_id}"
        )

        assert response.status_code == 200
        assert response.json() == []

    finally:
        delete_test_custom_list(list_id)
=======
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
>>>>>>> upstream/main


def test_get_nonexistent_favorite_list_returns_404():
    nonexistent_list_id = uuid.uuid4()

    response = client.get(
        f"/favorites/lists/{nonexistent_list_id}"
    )

    assert response.status_code == 404


<<<<<<< HEAD
# =========================================================
# 즐겨찾기 삭제 및 예외 테스트
# =========================================================


=======
>>>>>>> upstream/main
def test_delete_nonexistent_favorite_returns_404():
    nonexistent_favorite_id = uuid.uuid4()

    response = client.delete(
        f"/favorites/{nonexistent_favorite_id}"
    )

    assert response.status_code == 404


def test_create_favorite_with_nonexistent_facility_returns_404():
<<<<<<< HEAD
    custom_list = create_test_custom_list(
        prefix="없는 시설 테스트"
    )
    list_id = custom_list["id"]

    try:
        response = create_favorite(
            list_id=list_id,
            facility_id=str(uuid.uuid4()),
        )

        assert response.status_code == 404

    finally:
        delete_test_custom_list(list_id)


# =========================================================
# 중복 저장 테스트
# =========================================================


def test_duplicate_favorite_returns_409():
    custom_list = create_test_custom_list(
        prefix="중복 즐겨찾기 테스트"
    )
    list_id = custom_list["id"]

    facility_ids = create_test_facilities(1)
    facility_id = facility_ids[0]
=======
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
>>>>>>> upstream/main

    try:
        first_response = create_favorite(
            list_id=list_id,
            facility_id=facility_id,
        )

<<<<<<< HEAD
        assert first_response.status_code in (
            200,
            201,
        ), first_response.text

        first_data = first_response.json()

        assert first_data["list_id"] == list_id
        assert first_data["facility_id"] == facility_id

        second_response = create_favorite(
=======
        assert first_response.status_code in (200, 201)

        favorite_id = first_response.json()["id"]

        duplicate_response = create_favorite(
>>>>>>> upstream/main
            list_id=list_id,
            facility_id=facility_id,
        )

<<<<<<< HEAD
        assert second_response.status_code == 409
        assert (
            second_response.json()["detail"]
            == "해당 시설은 이미 이 목록에 저장되어 있습니다."
        )

    finally:
        delete_test_custom_list(list_id)
        delete_test_facilities(facility_ids)


# =========================================================
# 최신순 정렬 테스트
# =========================================================


def test_favorites_are_sorted_by_latest():
    custom_list = create_test_custom_list(
        prefix="최신순 정렬 테스트"
    )
    list_id = custom_list["id"]

    facility_ids = create_test_facilities(2)

    first_facility_id = facility_ids[0]
    second_facility_id = facility_ids[1]
=======
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
>>>>>>> upstream/main

    try:
        first_response = create_favorite(
            list_id=list_id,
<<<<<<< HEAD
            facility_id=first_facility_id,
        )

        assert first_response.status_code in (
            200,
            201,
        ), first_response.text

        first_favorite = first_response.json()

        # created_at 값이 구분되도록 약간 기다린다.
        time.sleep(0.2)

        second_response = create_favorite(
            list_id=list_id,
            facility_id=second_facility_id,
        )

        assert second_response.status_code in (
            200,
            201,
        ), second_response.text

        second_favorite = second_response.json()

        list_response = client.get(
            f"/favorites/lists/{list_id}"
        )

        assert list_response.status_code == 200

        favorites = list_response.json()

        assert len(favorites) == 2

        # 가장 나중에 저장한 즐겨찾기가 첫 번째여야 한다.
        assert (
            favorites[0]["id"]
            == second_favorite["id"]
        )
        assert (
            favorites[0]["facility_id"]
            == second_facility_id
        )

        # 먼저 저장한 즐겨찾기는 두 번째여야 한다.
        assert (
            favorites[1]["id"]
            == first_favorite["id"]
        )
        assert (
            favorites[1]["facility_id"]
            == first_facility_id
        )

        assert (
            favorites[0]["created_at"]
            >= favorites[1]["created_at"]
        )

    finally:
        delete_test_custom_list(list_id)
        delete_test_facilities(facility_ids)


# =========================================================
# 목록별 즐겨찾기 개수 테스트
# =========================================================


def test_favorite_count_matches_list_items():
    custom_list = create_test_custom_list(
        prefix="즐겨찾기 개수 테스트"
    )
    list_id = custom_list["id"]

    facility_ids = create_test_facilities(2)

    try:
        for facility_id in facility_ids:
            response = create_favorite(
                list_id=list_id,
                facility_id=facility_id,
            )

            assert response.status_code in (
                200,
                201,
            ), response.text

        lists_response = client.get(
            "/favorites/lists"
        )

        assert lists_response.status_code == 200

        favorite_lists = lists_response.json()

        target_list = next(
            favorite_list
            for favorite_list in favorite_lists
            if favorite_list["id"] == list_id
        )

        items_response = client.get(
            f"/favorites/lists/{list_id}"
        )

        assert items_response.status_code == 200

        items = items_response.json()

        assert target_list["favorite_count"] == 2
        assert target_list["favorite_count"] == len(items)

    finally:
        delete_test_custom_list(list_id)
        delete_test_facilities(facility_ids)

def test_create_custom_favorite_list():
    response = client.post(
        "/favorites/lists",
        json={
            "name": f"생성 테스트-{uuid.uuid4().hex[:8]}",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["list_type"] == "CUSTOM"
    assert data["name"] is not None
    assert data["favorite_count"] == 0

    delete_response = client.delete(
        f"/favorites/lists/{data['id']}"
    )

    assert delete_response.status_code == 204


def test_create_duplicate_custom_favorite_list_returns_409():
    list_name = f"중복 목록-{uuid.uuid4().hex[:8]}"

    first_response = client.post(
        "/favorites/lists",
        json={
            "name": list_name,
        },
    )

    assert first_response.status_code == 201, first_response.text

    list_id = first_response.json()["id"]

    try:
        second_response = client.post(
            "/favorites/lists",
            json={
                "name": list_name,
            },
        )

        assert second_response.status_code == 409
        assert (
            second_response.json()["detail"]
            == "같은 이름의 즐겨찾기 목록이 이미 존재합니다."
        )

    finally:
        delete_test_custom_list(list_id)


def test_update_custom_favorite_list():
    custom_list = create_test_custom_list(
        prefix="수정 전 목록"
    )
    list_id = custom_list["id"]

    try:
        new_name = f"수정 후 목록-{uuid.uuid4().hex[:8]}"

        response = client.patch(
            f"/favorites/lists/{list_id}",
            json={
                "name": new_name,
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["id"] == list_id
        assert data["list_type"] == "CUSTOM"
        assert data["name"] == new_name

    finally:
        delete_test_custom_list(list_id)


def test_update_basic_favorite_list_returns_400():
    favorite_lists = get_favorite_lists()

    basic_list = next(
        favorite_list
        for favorite_list in favorite_lists
        if favorite_list["list_type"] != "CUSTOM"
    )

    response = client.patch(
        f"/favorites/lists/{basic_list['id']}",
        json={
            "name": "기본 목록 수정 시도",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "기본 즐겨찾기 목록은 수정할 수 없습니다."
    )


def test_delete_custom_favorite_list():
    custom_list = create_test_custom_list(
        prefix="삭제 테스트"
    )
    list_id = custom_list["id"]

    response = client.delete(
        f"/favorites/lists/{list_id}"
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/favorites/lists/{list_id}"
    )

    assert get_response.status_code == 404


def test_delete_basic_favorite_list_returns_400():
    favorite_lists = get_favorite_lists()

    basic_list = next(
        favorite_list
        for favorite_list in favorite_lists
        if favorite_list["list_type"] != "CUSTOM"
    )

    response = client.delete(
        f"/favorites/lists/{basic_list['id']}"
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "기본 즐겨찾기 목록은 삭제할 수 없습니다."
    )
=======
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


def test_favorite_count_matches_list_items():
    favorite_lists = get_favorite_lists()

    for favorite_list in favorite_lists:
        response = client.get(
            f"/favorites/lists/{favorite_list['id']}"
        )

        assert response.status_code == 200
        assert favorite_list["favorite_count"] == len(response.json())
>>>>>>> upstream/main
