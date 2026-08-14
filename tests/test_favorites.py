import time
import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.deps import MOCK_USER_ID
from app.main import app
from app.models.facility import Facility
from app.models.favorite import Favorite


# 실 인증 연결 후엔 Authorization 헤더 없이는 전부 401이라, mock 유저로 진짜
# access token을 발급받아 TestClient 기본 헤더로 박아둔다.
client = TestClient(
    app,
    headers={"Authorization": f"Bearer {create_access_token(MOCK_USER_ID)}"},
)


# =========================================================
# 공통 헬퍼 함수
# =========================================================


def get_favorite_lists() -> list[dict]:
    """현재 Mock 사용자의 즐겨찾기 목록을 조회한다."""
    response = client.get("/favorites/lists")

    assert response.status_code == 200, response.text

    return response.json()


def get_list_id(list_type: str) -> str:
    """고정 즐겨찾기 목록 타입으로 list_id를 찾는다."""
    favorite_lists = get_favorite_lists()

    favorite_list = next(
        item
        for item in favorite_lists
        if item["list_type"] == list_type
    )

    return favorite_list["id"]


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
    """테스트에서 생성한 시설과 연결된 즐겨찾기를 삭제한다."""
    if not facility_ids:
        return

    db = SessionLocal()

    try:
        (
            db.query(Favorite)
            .filter(
                Favorite.facility_id.in_(facility_ids)
            )
            .delete(
                synchronize_session=False
            )
        )

        uuid_ids = [
            uuid.UUID(facility_id)
            for facility_id in facility_ids
        ]

        (
            db.query(Facility)
            .filter(
                Facility.id.in_(uuid_ids)
            )
            .delete(
                synchronize_session=False
            )
        )

        db.commit()

    finally:
        db.close()


def create_favorite(
    list_id: str,
    facility_id: str,
    source: str = "internal",
):
    """전달받은 목록에 시설을 즐겨찾기로 저장한다."""
    return client.post(
        "/favorites",
        json={
            "list_id": list_id,
            "facility_id": facility_id,
            "source": source,
        },
    )


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


def test_get_favorite_lists():
    response = client.get(
        "/favorites/lists"
    )

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
        assert "created_at" in item
        assert "favorite_count" in item

        assert isinstance(
            item["favorite_count"],
            int,
        )


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


# =========================================================
# 예외 처리 테스트
# =========================================================


def test_delete_nonexistent_favorite_returns_404():
    nonexistent_favorite_id = uuid.uuid4()

    response = client.delete(
        f"/favorites/{nonexistent_favorite_id}"
    )

    assert response.status_code == 404


def test_create_favorite_with_nonexistent_facility_returns_404():
    list_id = get_list_id(
        "FREQUENT"
    )

    response = create_favorite(
        list_id=list_id,
        facility_id=str(uuid.uuid4()),
    )

    assert response.status_code == 404


def test_create_favorite_with_non_uuid_internal_facility_id_returns_422():
    list_id = get_list_id(
        "FREQUENT"
    )

    response = create_favorite(
        list_id=list_id,
        facility_id="521460056",  # 카카오 place id 형식, internal 소스엔 부적합
        source="internal",
    )

    assert response.status_code == 422


# =========================================================
# 중복 저장 테스트
# =========================================================


def test_duplicate_favorite_returns_409():
    list_id = get_list_id(
        "FREQUENT"
    )

    facility_ids = create_test_facilities(1)
    facility_id = facility_ids[0]

    favorite_id = None

    try:
        first_response = create_favorite(
            list_id=list_id,
            facility_id=facility_id,
        )

        assert first_response.status_code in (
            200,
            201,
        ), first_response.text

        first_data = first_response.json()
        favorite_id = first_data["id"]

        assert first_data["list_id"] == list_id
        assert (
            first_data["facility_id"]
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
        if favorite_id is not None:
            delete_favorite(
                favorite_id
            )

        delete_test_facilities(
            facility_ids
        )


# =========================================================
# 최신순 정렬 테스트
# =========================================================


def test_favorites_are_sorted_by_latest():
    list_id = get_list_id(
        "FREQUENT"
    )

    facility_ids = create_test_facilities(2)

    created_favorite_ids = []

    try:
        first_response = create_favorite(
            list_id=list_id,
            facility_id=facility_ids[0],
        )

        assert first_response.status_code in (
            200,
            201,
        ), first_response.text

        created_favorite_ids.append(
            first_response.json()["id"]
        )

        time.sleep(0.1)

        second_response = create_favorite(
            list_id=list_id,
            facility_id=facility_ids[1],
        )

        assert second_response.status_code in (
            200,
            201,
        ), second_response.text

        created_favorite_ids.append(
            second_response.json()["id"]
        )

        response = client.get(
            f"/favorites/lists/{list_id}"
        )

        assert response.status_code == 200

        created_favorites = [
            favorite
            for favorite in response.json()
            if favorite["id"]
            in created_favorite_ids
        ]

        assert len(
            created_favorites
        ) == 2

        created_at_values = [
            datetime.fromisoformat(
                favorite["created_at"].replace(
                    "Z",
                    "+00:00",
                )
            )
            for favorite
            in created_favorites
        ]

        assert created_at_values == sorted(
            created_at_values,
            reverse=True,
        )

        assert (
            created_favorites[0]["id"]
            == created_favorite_ids[1]
        )

        assert (
            created_favorites[1]["id"]
            == created_favorite_ids[0]
        )

    finally:
        for favorite_id in created_favorite_ids:
            delete_response = delete_favorite(
                favorite_id
            )

            assert delete_response.status_code in (
                200,
                204,
                404,
            )

        delete_test_facilities(
            facility_ids
        )


# =========================================================
# favorite_count 테스트
# =========================================================


def test_favorite_count_matches_list_items():
    favorite_lists = get_favorite_lists()

    for favorite_list in favorite_lists:
        response = client.get(
            f"/favorites/lists/{favorite_list['id']}"
        )

        assert response.status_code == 200

        assert (
            favorite_list["favorite_count"]
            == len(response.json())
        )


# =========================================================
# 같은 시설을 여러 목록에 저장하는 테스트
# =========================================================


def test_same_facility_can_be_saved_to_different_lists():
    frequent_list_id = get_list_id(
        "FREQUENT"
    )

    wishlist_list_id = get_list_id(
        "WISHLIST"
    )

    facility_ids = create_test_facilities(1)
    facility_id = facility_ids[0]

    created_favorite_ids = []

    try:
        first_response = create_favorite(
            list_id=frequent_list_id,
            facility_id=facility_id,
        )

        assert first_response.status_code in (
            200,
            201,
        ), first_response.text

        created_favorite_ids.append(
            first_response.json()["id"]
        )

        second_response = create_favorite(
            list_id=wishlist_list_id,
            facility_id=facility_id,
        )

        assert second_response.status_code in (
            200,
            201,
        ), second_response.text

        created_favorite_ids.append(
            second_response.json()["id"]
        )

        assert (
            first_response.json()["list_id"]
            == frequent_list_id
        )

        assert (
            second_response.json()["list_id"]
            == wishlist_list_id
        )

        assert (
            first_response.json()["facility_id"]
            == facility_id
        )

        assert (
            second_response.json()["facility_id"]
            == facility_id
        )

    finally:
        for favorite_id in created_favorite_ids:
            delete_favorite(
                favorite_id
            )

        delete_test_facilities(
            facility_ids
        )


# =========================================================
# 즐겨찾기 상태 조회 테스트
# =========================================================


def test_favorite_status_returns_all_list_ids():
    frequent_list_id = get_list_id(
        "FREQUENT"
    )

    wishlist_list_id = get_list_id(
        "WISHLIST"
    )

    facility_ids = create_test_facilities(1)
    facility_id = facility_ids[0]

    created_favorite_ids = []

    try:
        first_response = create_favorite(
            list_id=frequent_list_id,
            facility_id=facility_id,
        )

        assert first_response.status_code in (
            200,
            201,
        ), first_response.text

        created_favorite_ids.append(
            first_response.json()["id"]
        )

        second_response = create_favorite(
            list_id=wishlist_list_id,
            facility_id=facility_id,
        )

        assert second_response.status_code in (
            200,
            201,
        ), second_response.text

        created_favorite_ids.append(
            second_response.json()["id"]
        )

        status_response = client.get(
            "/favorites/status",
            params={
                "facility_id": facility_id,
            },
        )

        assert status_response.status_code == 200

        data = status_response.json()

        assert data["is_favorite"] is True

        assert set(
            data["favorite_list_ids"]
        ) == {
            frequent_list_id,
            wishlist_list_id,
        }

    finally:
        for favorite_id in created_favorite_ids:
            delete_favorite(
                favorite_id
            )

        delete_test_facilities(
            facility_ids
        )


# =========================================================
# 카카오 소스(source=kakao) 테스트
# =========================================================


def test_create_kakao_favorite_skips_existence_check():
    """kakao 소스는 내부 DB에 없는 place id라도 재조회 없이 저장을 허용한다."""
    list_id = get_list_id("FREQUENT")
    facility_id = f"kakao-test-{uuid.uuid4().hex[:8]}"
    favorite_id = None

    try:
        response = create_favorite(
            list_id=list_id,
            facility_id=facility_id,
            source="kakao",
        )

        assert response.status_code == 201, response.text

        body = response.json()
        assert body["facility_id"] == facility_id
        assert body["source"] == "kakao"

        favorite_id = body["id"]

        status_response = client.get(
            "/favorites/status",
            params={
                "facility_id": facility_id,
                "source": "kakao",
            },
        )

        assert status_response.status_code == 200
        assert status_response.json()["is_favorite"] is True

    finally:
        if favorite_id is not None:
            delete_favorite(favorite_id)
