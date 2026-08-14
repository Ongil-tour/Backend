"""
auth.py / oauth.py / security.py 테스트.
실제 OAuth provider 서버는 호출하지 않고, provider 함수를 monkeypatch로 대체한다.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import JWTError

from app.core.database import SessionLocal
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.crud import auth as crud_auth
from app.main import app
from app.models.favorite import FavoriteList
from app.models.user import RefreshToken, SocialAccount, User


client = TestClient(app)


# =========================================================
# security.py - JWT 인코딩/디코딩
# =========================================================


def test_access_token_round_trip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)

    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_refresh_token_round_trip():
    user_id = uuid.uuid4()
    token = create_refresh_token(user_id)

    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"


def test_decode_invalid_token_raises_jwt_error():
    with pytest.raises(JWTError):
        decode_token("this-is-not-a-valid-token")


# =========================================================
# crud/auth.py - refresh_token 저장/조회/삭제
# =========================================================


def test_get_valid_refresh_token_returns_none_when_expired():
    db = SessionLocal()
    user_id = uuid.uuid4()
    token = "expired-token-" + uuid.uuid4().hex

    try:
        db.add(User(id=user_id, email=f"expired-{uuid.uuid4().hex[:8]}@example.com"))
        db.commit()

        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        crud_auth.save_refresh_token(db, user_id=user_id, token=token, expires_at=past)

        assert crud_auth.get_valid_refresh_token(db, token) is None

    finally:
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
        db.close()


# =========================================================
# 테스트 헬퍼: 실제 provider 호출을 흉내내는 monkeypatch
# =========================================================


def _cleanup_user_by_email(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is not None:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def _patch_google_provider(monkeypatch, provider_user_id: str, email: str):
    """구글은 idToken 검증 방식이라 verify_google_id_token 하나만 갈아끼우면 됨."""

    async def fake_verify_id_token(id_token):
        return {"provider_user_id": provider_user_id, "email": email}

    monkeypatch.setattr("app.routers.auth.verify_google_id_token", fake_verify_id_token)


def _patch_kakao_provider(monkeypatch, provider_user_id: str, email: str):
    async def fake_get_access_token(code):
        return "fake-kakao-access-token"

    async def fake_get_user_info(token):
        return {"provider_user_id": provider_user_id, "email": email}

    monkeypatch.setattr("app.routers.auth.get_kakao_access_token", fake_get_access_token)
    monkeypatch.setattr("app.routers.auth.get_kakao_user_info", fake_get_user_info)


# =========================================================
# POST /auth/{provider}/callback
# =========================================================


def test_callback_creates_new_user_with_three_favorite_lists(monkeypatch):
    """신규 유저 최초 로그인 시 User + SocialAccount + 즐겨찾기 목록 3개가 생성돼야 한다."""
    email = f"new-{uuid.uuid4().hex[:8]}@example.com"
    _patch_google_provider(monkeypatch, provider_user_id=f"google-{uuid.uuid4().hex[:8]}", email=email)

    try:
        response = client.post("/auth/google/callback", json={"id_token": "fake-id-token"})

        assert response.status_code == 200, response.text
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            assert user is not None

            favorite_lists = (
                db.query(FavoriteList).filter(FavoriteList.user_id == user.id).all()
            )
            assert len(favorite_lists) == 3
            assert {fl.list_type for fl in favorite_lists} == {
                "FREQUENT",
                "WISHLIST",
                "VISITED",
            }

            social_account = (
                db.query(SocialAccount)
                .filter(SocialAccount.user_id == user.id)
                .first()
            )
            assert social_account is not None
            assert social_account.provider == "google"
        finally:
            db.close()

    finally:
        _cleanup_user_by_email(email)


def test_callback_existing_social_account_reuses_same_user(monkeypatch):
    """이미 연동된 소셜 계정으로 다시 로그인하면 유저가 새로 생기지 않고 토큰만 재발급돼야 한다."""
    email = f"existing-{uuid.uuid4().hex[:8]}@example.com"
    provider_user_id = f"google-{uuid.uuid4().hex[:8]}"
    _patch_google_provider(monkeypatch, provider_user_id=provider_user_id, email=email)

    try:
        first_response = client.post("/auth/google/callback", json={"id_token": "fake-id-token-1"})
        assert first_response.status_code == 200, first_response.text

        db = SessionLocal()
        try:
            assert db.query(User).filter(User.email == email).count() == 1
        finally:
            db.close()

        second_response = client.post("/auth/google/callback", json={"id_token": "fake-id-token-2"})
        assert second_response.status_code == 200, second_response.text

        db = SessionLocal()
        try:
            assert db.query(User).filter(User.email == email).count() == 1
        finally:
            db.close()

    finally:
        _cleanup_user_by_email(email)


def test_callback_same_email_different_provider_links_account(monkeypatch):
    """같은 이메일로 다른 provider 로그인 시 500 대신 기존 계정에 연동되어야 한다."""
    email = f"linked-{uuid.uuid4().hex[:8]}@example.com"

    _patch_kakao_provider(monkeypatch, provider_user_id=f"kakao-{uuid.uuid4().hex[:8]}", email=email)
    first_response = client.post("/auth/kakao/callback", json={"code": "fake-code"})
    assert first_response.status_code == 200, first_response.text

    try:
        _patch_google_provider(
            monkeypatch, provider_user_id=f"google-{uuid.uuid4().hex[:8]}", email=email
        )
        second_response = client.post("/auth/google/callback", json={"id_token": "fake-id-token"})

        assert second_response.status_code == 200, second_response.text

        db = SessionLocal()
        try:
            users = db.query(User).filter(User.email == email).all()
            assert len(users) == 1

            providers = {
                social_account.provider
                for social_account in db.query(SocialAccount).filter(
                    SocialAccount.user_id == users[0].id
                )
            }
            assert providers == {"kakao", "google"}

            # 계정을 연동해도 즐겨찾기 목록은 최초 가입 때 만든 3개 그대로여야 함 (중복 생성 X)
            favorite_lists = (
                db.query(FavoriteList).filter(FavoriteList.user_id == users[0].id).all()
            )
            assert len(favorite_lists) == 3
        finally:
            db.close()

    finally:
        _cleanup_user_by_email(email)


def test_callback_unsupported_provider_returns_400():
    response = client.post("/auth/unknown/callback", json={"code": "fake-code"})
    assert response.status_code == 400


def test_callback_google_without_id_token_returns_422():
    """구글 로그인인데 id_token을 안 보내면 422여야 한다."""
    response = client.post("/auth/google/callback", json={"code": "fake-code"})
    assert response.status_code == 422


def test_callback_kakao_without_code_returns_422():
    """카카오 로그인인데 code를 안 보내면 422여야 한다."""
    response = client.post("/auth/kakao/callback", json={"id_token": "fake-id-token"})
    assert response.status_code == 422


# =========================================================
# POST /auth/refresh, POST /auth/logout
# =========================================================


def test_refresh_rotates_token_and_invalidates_old_one():
    user_id = uuid.uuid4()
    old_refresh = create_refresh_token(user_id)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)

    # User와 RefreshToken을 한 commit에 같이 넣으면 ORM에 relationship()이
    # 없어서 FK 순서를 보장 못 해줌 -> User부터 따로 커밋.
    db = SessionLocal()
    try:
        db.add(User(id=user_id, email=f"refresh-{uuid.uuid4().hex[:8]}@example.com"))
        db.commit()

        db.add(RefreshToken(user_id=user_id, token=old_refresh, expires_at=expires_at))
        db.commit()
    finally:
        db.close()

    try:
        response = client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert response.status_code == 200, response.text

        new_tokens = response.json()
        assert new_tokens["refresh_token"] != old_refresh

        # rolling 방식이므로 기존 refresh token은 재사용 불가능해야 함
        reuse_response = client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert reuse_response.status_code == 401

    finally:
        db = SessionLocal()
        try:
            db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
            db.query(User).filter(User.id == user_id).delete()
            db.commit()
        finally:
            db.close()


def test_refresh_with_invalid_token_returns_401():
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


def test_refresh_with_access_token_type_returns_401():
    """access token을 refresh 엔드포인트에 넣으면 거부돼야 한다."""
    user_id = uuid.uuid4()
    access_token = create_access_token(user_id)

    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


def test_logout_deletes_refresh_token():
    user_id = uuid.uuid4()
    token = create_refresh_token(user_id)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)

    db = SessionLocal()
    try:
        db.add(User(id=user_id, email=f"logout-{uuid.uuid4().hex[:8]}@example.com"))
        db.commit()

        db.add(RefreshToken(user_id=user_id, token=token, expires_at=expires_at))
        db.commit()
    finally:
        db.close()

    try:
        response = client.post("/auth/logout", json={"refresh_token": token})
        assert response.status_code == 200

        db = SessionLocal()
        try:
            assert db.query(RefreshToken).filter(RefreshToken.token == token).first() is None
        finally:
            db.close()
    finally:
        db = SessionLocal()
        try:
            db.query(User).filter(User.id == user_id).delete()
            db.commit()
        finally:
            db.close()
