import pytest
import uuid
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# ─── Health Check ───────────────────────────────────────────────

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json == {"status": "ok"}

# ─── Event Creation (Happy Path) ───────────────────────────────

def test_create_event(client):
    event_name = f"Event_{uuid.uuid4()}"
    res = client.post("/admin/event", json={
        "name": event_name,
        "total_tickets": 10
    })
    assert res.status_code == 201
    assert res.json["name"] == event_name
    assert res.json["total_tickets"] == 10
    assert res.json["available_tickets"] == 10

# ─── Event Creation (Edge Cases) ──────────────────────────────

def test_create_event_duplicate_name(client):
    name = f"Dup_{uuid.uuid4()}"
    client.post("/admin/event", json={"name": name, "total_tickets": 5})
    res = client.post("/admin/event", json={"name": name, "total_tickets": 5})
    assert res.status_code == 400
    assert "already exists" in res.json["error"]

def test_create_event_missing_name(client):
    res = client.post("/admin/event", json={"total_tickets": 10})
    assert res.status_code == 400

def test_create_event_missing_tickets(client):
    res = client.post("/admin/event", json={"name": f"E_{uuid.uuid4()}"})
    assert res.status_code == 400

def test_create_event_zero_tickets(client):
    res = client.post("/admin/event", json={"name": f"E_{uuid.uuid4()}", "total_tickets": 0})
    assert res.status_code == 400

def test_create_event_negative_tickets(client):
    res = client.post("/admin/event", json={"name": f"E_{uuid.uuid4()}", "total_tickets": -5})
    assert res.status_code == 400

def test_create_event_string_tickets(client):
    res = client.post("/admin/event", json={"name": f"E_{uuid.uuid4()}", "total_tickets": "ten"})
    assert res.status_code == 400

def test_create_event_empty_body(client):
    res = client.post("/admin/event", data="not json", content_type="text/plain")
    assert res.status_code == 400

def test_create_event_empty_name(client):
    res = client.post("/admin/event", json={"name": "", "total_tickets": 10})
    assert res.status_code == 400

# ─── Reservation (Happy Path) ─────────────────────────────────

def test_reservation_flow(client):
    event_name = f"Test_{uuid.uuid4()}"
    res = client.post("/admin/event", json={"name": event_name, "total_tickets": 10})
    assert res.status_code == 201
    event_id = res.json["id"]

    res = client.post("/reserve", json={"event_id": event_id, "user_email": "buy1@test.com"})
    assert res.status_code == 201
    assert res.json["message"] == "Reservation successful"
    assert res.json["reservation"]["event"]["available_tickets"] == 9

    res_two = client.post("/reserve", json={"event_id": event_id, "user_email": "buy2@test.com"})
    assert res_two.status_code == 201
    assert res_two.json["reservation"]["event"]["available_tickets"] == 8

# ─── Reservation (Edge Cases) ─────────────────────────────────

def test_reserve_nonexistent_event(client):
    res = client.post("/reserve", json={"event_id": 999999, "user_email": "x@test.com"})
    assert res.status_code == 404
    assert "not found" in res.json["error"]

def test_reserve_missing_event_id(client):
    res = client.post("/reserve", json={"user_email": "x@test.com"})
    assert res.status_code == 400

def test_reserve_missing_email(client):
    res = client.post("/reserve", json={"event_id": 1})
    assert res.status_code == 400

def test_reserve_invalid_email(client):
    name = f"E_{uuid.uuid4()}"
    res = client.post("/admin/event", json={"name": name, "total_tickets": 5})
    eid = res.json["id"]
    res = client.post("/reserve", json={"event_id": eid, "user_email": "not-an-email"})
    assert res.status_code == 400
    assert "email" in res.json["error"].lower()

def test_reserve_duplicate_user(client):
    name = f"E_{uuid.uuid4()}"
    res = client.post("/admin/event", json={"name": name, "total_tickets": 5})
    eid = res.json["id"]

    res1 = client.post("/reserve", json={"event_id": eid, "user_email": "dup@test.com"})
    assert res1.status_code == 201

    res2 = client.post("/reserve", json={"event_id": eid, "user_email": "dup@test.com"})
    assert res2.status_code == 409
    assert "already has a reservation" in res2.json["error"]

def test_reserve_sold_out(client):
    name = f"E_{uuid.uuid4()}"
    res = client.post("/admin/event", json={"name": name, "total_tickets": 1})
    eid = res.json["id"]

    res1 = client.post("/reserve", json={"event_id": eid, "user_email": "first@test.com"})
    assert res1.status_code == 201

    res2 = client.post("/reserve", json={"event_id": eid, "user_email": "second@test.com"})
    assert res2.status_code == 400
    assert "Sold out" in res2.json["error"]

def test_reserve_empty_body(client):
    res = client.post("/reserve", data="garbage", content_type="text/plain")
    assert res.status_code == 400

# ─── 404 Handling ──────────────────────────────────────────────

def test_404_returns_json(client):
    res = client.get("/nonexistent-route")
    assert res.status_code == 404
    assert res.content_type == "application/json"
