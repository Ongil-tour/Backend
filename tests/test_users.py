"""
users.py 엔드포인트 테스트.
"""
import uuid

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.main import app
from app.models.user import User, UserSettings
from app.deps import MOCK_USER_ID
from app.scripts.seed import seed


client = TestClient(
    app,
    headers={"Authorization": f"Bearer {create_access_token(MOCK_USER_ID)}"},
)


def get_my_settings():
    """현재 mock 유저의 설정을 원래 상태로 저장해두기 위한 헬퍼."""
    db = SessionLocal()
    try:
        return db.query(UserSettings).filter(UserSettings.user_id == MOCK_USER_ID).first()
    finally:
        db.close()


def test_patch_settings_success():
    """PATCH /users/me - 정상적인 값으로 요청하면 200과 함께 변경된 값이 와야 함."""
    response = client.patch("/users/me", json={"font_size": "lg", "dark_mode": True})

    assert response.status_code == 200
    data = response.json()
    assert data["font_size"] == "lg"
    assert data["dark_mode"] is True

    # 테스트가 남긴 변경사항을 원래 값으로 되돌려놓기 (다른 테스트/작업에 영향 안 주게)
    client.patch("/users/me", json={"font_size": "md", "dark_mode": False})


def test_patch_settings_all_profile_images_accepted():
    """PATCH /users/me - 허용된 profile_image 4종이 전부 통과해야 함 (오타로 하나만 막히던 버그 재발 방지)."""
    for profile_image in ["profile1.png", "profile2.png", "profile3.png", "profile4.png"]:
        response = client.patch("/users/me", json={"profile_image": profile_image})
        assert response.status_code == 200, response.text
        assert response.json()["profile_image"] == profile_image

    # 원래 값으로 되돌려놓기
    client.patch("/users/me", json={"profile_image": "profile1.png"})


def test_patch_settings_invalid_font_size_returns_422():
    """PATCH /users/me - 허용 안 된 font_size 값을 보내면 422가 와야 함."""
    response = client.patch("/users/me", json={"font_size": "extra_large"})

    assert response.status_code == 422


def test_delete_user_removes_cascaded_data():
    """
    DELETE /users/me - 유저 삭제 시 user_settings도 같이 지워져야 함 (CASCADE 확인).
    ⚠️ mock 유저는 다른 테스트 파일(예: test_favorites.py)에서도 공유해서 쓰는 유저라서,
    테스트가 끝나면 반드시 seed()로 "완전히" 복구해야 한다.
    User row만 다시 만들면 SocialAccount/UserSettings/FavoriteList 3개가 없는 채로
    남아서 다른 테스트가 깨진다 (예: 즐겨찾기 목록 3개 조회가 빈 배열이 됨).
    """
    db = SessionLocal()
    try:
        user_before = db.query(User).filter(User.id == MOCK_USER_ID).first()
        assert user_before is not None  # 삭제 전 mock 유저가 있어야 테스트 의미 있음
    finally:
        db.close()

    response = client.delete("/users/me")
    assert response.status_code == 204

    db = SessionLocal()
    try:
        assert db.query(User).filter(User.id == MOCK_USER_ID).first() is None
        assert db.query(UserSettings).filter(UserSettings.user_id == MOCK_USER_ID).first() is None
    finally:
        db.close()
        # mock 유저 + SocialAccount + 즐겨찾기 목록 3개까지 전부 원상복구
        seed()