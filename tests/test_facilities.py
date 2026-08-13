import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_barrier_free_facility_not_found():
    facility_id = uuid.uuid4()

    response = client.get(
        f"/facilities/{facility_id}/barrier-free"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "facility not found"

from app.core.database import SessionLocal
from app.models.facility import Facility


def test_get_barrier_free_facility():
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

        assert data["wheelchairAccessible"] is True
        assert data["disabledRestroom"] is True
        assert data["parkingLot"] is True
        assert data["elevator"] is False
        assert data["petFriendly"] is False
        assert data["nursingRoom"] is True

    finally:
        db.delete(facility)
        db.commit()
        db.close()