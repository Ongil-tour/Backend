"""
users.py 엔드포인트 테스트.
"""
import uuid

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.user import User, UserSettings
from app.deps import MOCK_USER_ID


client = TestClient(app)


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


def test_patch_settings_invalid_font_size_returns_422():
    """PATCH /users/me - 허용 안 된 font_size 값을 보내면 422가 와야 함."""
    response = client.patch("/users/me", json={"font_size": "extra_large"})

    assert response.status_code == 422


def test_delete_user_removes_cascaded_data():
    """
    DELETE /users/me - 유저 삭제 시 user_settings도 같이 지워져야 함 (CASCADE 확인).
    ⚠️ mock 유저는 다른 작업(Swagger 수동 테스트 등)에서도 공유해서 쓰는 유저라서,
    테스트가 끝나면 반드시 다시 시드해서 복구해야 함.
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

        # mock 유저 복구 (다음 테스트, 다음 Swagger 수동 테스트를 위해)
        db2 = SessionLocal()
        try:
            db2.add(User(id=MOCK_USER_ID, email="mock@example.com"))
            db2.commit()
        finally:
            db2.close()