"""
실 사용자 2명 기준 격리 테스트.
memory에 "인증 도입 후 세트로 확인 필요"로 남아있던 항목 -
mock 유저 하나로만 돌아가던 test_favorites.py와 달리, 실제로 서로 다른
user_id 토큰 2개를 만들어서 다른 사람의 list_id/favorite_id에 접근하면
404가 나는지 확인한다.
"""
import uuid

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.main import app
from app.models.facility import Facility
from app.models.favorite import FavoriteList, ListType
from app.models.user import User


client = TestClient(app)


def _create_user_with_favorite_list() -> tuple[str, str, uuid.UUID]:
    """새 유저 + FREQUENT 목록 1개를 만들고 (access_token, list_id, user_id)를 반환."""
    db = SessionLocal()
    try:
        user = User(email=f"isolation-{uuid.uuid4().hex[:8]}@example.com")
        db.add(user)
        db.flush()

        favorite_list = FavoriteList(user_id=user.id, list_type=ListType.FREQUENT.value)
        db.add(favorite_list)
        db.commit()
        db.refresh(favorite_list)

        token = create_access_token(user.id)
        return token, str(favorite_list.id), user.id
    finally:
        db.close()


def _cleanup_user(user_id: uuid.UUID):
    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


def test_user_cannot_read_another_users_favorite_list():
    token_a, list_id_a, user_id_a = _create_user_with_favorite_list()
    token_b, _list_id_b, user_id_b = _create_user_with_favorite_list()

    try:
        # B의 토큰으로 A의 리스트를 조회하면 404 (남의 목록 존재 자체를 노출하지 않음)
        response = client.get(
            f"/favorites/lists/{list_id_a}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404

        # A 본인 토큰으로는 정상 조회
        own_response = client.get(
            f"/favorites/lists/{list_id_a}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert own_response.status_code == 200

    finally:
        _cleanup_user(user_id_a)
        _cleanup_user(user_id_b)


def test_user_cannot_save_favorite_to_another_users_list():
    token_a, list_id_a, user_id_a = _create_user_with_favorite_list()
    token_b, _list_id_b, user_id_b = _create_user_with_favorite_list()

    db = SessionLocal()
    try:
        facility = Facility(
            content_id=uuid.uuid4().hex[:20],
            content_type_id="12",
            name="격리 테스트 시설",
            category="관광지",
            address="테스트 주소",
            lat=35.1796,
            lng=129.0756,
        )
        db.add(facility)
        db.commit()
        db.refresh(facility)
        facility_id = str(facility.id)
    finally:
        db.close()

    try:
        # B가 A의 list_id에 저장을 시도하면 404 (B 소유가 아니므로)
        response = client.post(
            "/favorites",
            json={"facility_id": facility_id, "list_id": list_id_a},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 404

    finally:
        db = SessionLocal()
        try:
            db.query(Facility).filter(Facility.id == uuid.UUID(facility_id)).delete()
            db.commit()
        finally:
            db.close()
        _cleanup_user(user_id_a)
        _cleanup_user(user_id_b)


def test_user_cannot_delete_another_users_favorite():
    token_a, list_id_a, user_id_a = _create_user_with_favorite_list()
    token_b, _list_id_b, user_id_b = _create_user_with_favorite_list()

    db = SessionLocal()
    try:
        facility = Facility(
            content_id=uuid.uuid4().hex[:20],
            content_type_id="12",
            name="격리 테스트 시설2",
            category="관광지",
            address="테스트 주소",
            lat=35.18,
            lng=129.08,
        )
        db.add(facility)
        db.commit()
        db.refresh(facility)
        facility_id = str(facility.id)
    finally:
        db.close()

    try:
        create_response = client.post(
            "/favorites",
            json={"facility_id": facility_id, "list_id": list_id_a},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert create_response.status_code == 201
        favorite_id = create_response.json()["id"]

        # B가 A의 favorite_id를 삭제하려 하면 404
        delete_response = client.delete(
            f"/favorites/{favorite_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert delete_response.status_code == 404

        # A 본인은 정상 삭제 가능
        own_delete_response = client.delete(
            f"/favorites/{favorite_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert own_delete_response.status_code == 204

    finally:
        db = SessionLocal()
        try:
            db.query(Facility).filter(Facility.id == uuid.UUID(facility_id)).delete()
            db.commit()
        finally:
            db.close()
        _cleanup_user(user_id_a)
        _cleanup_user(user_id_b)
