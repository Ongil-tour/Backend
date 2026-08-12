import uuid

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.facility import Facility


client = TestClient(app)


def test_get_barrier_free_info():
    db = SessionLocal()

    try:
        facility = db.query(Facility).first()
        assert facility is not None

        facility_id = str(facility.id)

    finally:
        db.close()

    response = client.get(
        f"/facilities/{facility_id}/barrier-free"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["facility_id"] == facility_id
    assert "wheelchair_accessible" in data
    assert "disabled_restroom" in data
    assert "disabled_parking" in data
    assert "elevator" in data
    assert "pet_friendly" in data
    assert "nursing_room" in data
    assert "synced_at" in data


def test_get_nonexistent_barrier_free_info_returns_404():
    nonexistent_id = uuid.uuid4()

    response = client.get(
        f"/facilities/{nonexistent_id}/barrier-free"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "facility not found"