"""
app/deps.py::get_current_user 테스트.
favorites/users 라우터가 공통으로 쓰는 인증 의존성 자체를 검증한다.
편의상 GET /favorites/lists를 보호된 엔드포인트 대표로 사용.
"""
import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token, create_refresh_token
from app.deps import MOCK_USER_ID
from app.main import app


# 이 파일은 "인증 자체가 없을 때/틀렸을 때"를 확인하는 게 목적이라
# 기본 Authorization 헤더를 안 박아두고 요청마다 따로 넣는다.
client = TestClient(app)


def test_protected_endpoint_without_token_returns_401():
    response = client.get("/favorites/lists")

    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


def test_protected_endpoint_with_garbage_token_returns_401():
    response = client.get(
        "/favorites/lists",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_protected_endpoint_with_refresh_token_returns_401():
    """access token 자리에 refresh token을 넣으면 거부돼야 한다."""
    refresh_token = create_refresh_token(MOCK_USER_ID)

    response = client.get(
        "/favorites/lists",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 401


def test_protected_endpoint_with_nonexistent_user_returns_401():
    access_token = create_access_token(uuid.uuid4())

    response = client.get(
        "/favorites/lists",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 401


def test_protected_endpoint_with_valid_token_returns_200():
    access_token = create_access_token(MOCK_USER_ID)

    response = client.get(
        "/favorites/lists",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
