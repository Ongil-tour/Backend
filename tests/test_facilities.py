import uuid

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.facility import Facility


client = TestClient(app)


def test_get_barrier_free_info():
    db = SessionLocal()

    facility = Facility(
        content_id=uuid.uuid4().hex[:20],
        content_type_id="12",
        name="배리어프리 테스트 시설",
        category="관광지",
        address="테스트 주소",
        lat=35.1796,
        lng=129.0756,
        wheelchair_accessible=True,
        disabled_restroom=True,
        disabled_parking=True,
        elevator=False,
        pet_friendly=False,
        nursing_room=True,
    )

    try:
        db.add(facility)
        db.commit()
        db.refresh(facility)

        response = client.get(
            f"/facilities/{facility.id}/barrier-free"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["facility_id"] == str(facility.id)
        assert data["wheelchair_accessible"] is True
        assert data["disabled_restroom"] is True
        assert data["disabled_parking"] is True
        assert data["elevator"] is False
        assert data["pet_friendly"] is False
        assert data["nursing_room"] is True
        assert "synced_at" in data

    finally:
        db.delete(facility)
        db.commit()
        db.close()


def test_get_nonexistent_barrier_free_info_returns_404():
    nonexistent_id = uuid.uuid4()

    response = client.get(
        f"/facilities/{nonexistent_id}/barrier-free"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "facility not found"