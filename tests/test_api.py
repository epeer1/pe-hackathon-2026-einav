import pytest
import uuid
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json == {"status": "ok"}

def test_reservation_flow(client):
    event_name = f"Test_{uuid.uuid4()}"
    
    # 1. Create novel event
    res = client.post("/admin/event", json={
        "name": event_name,
        "total_tickets": 10
    })
    assert res.status_code == 201
    event_id = res.json["id"]

    # 2. Reserve a ticket
    res = client.post("/reserve", json={
        "event_id": event_id,
        "user_email": "buy1@test.com"
    })
    assert res.status_code == 201
    assert res.json["message"] == "Reservation successful"
    assert res.json["reservation"]["event"]["available_tickets"] == 9

    # 3. Reserve a second ticket
    res_two = client.post("/reserve", json={
        "event_id": event_id,
        "user_email": "buy2@test.com"
    })
    assert res_two.status_code == 201
    assert res_two.json["reservation"]["event"]["available_tickets"] == 8
