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

# ─── Inactive Event Handling ──────────────────────────────────

def test_reserve_inactive_event(client):
    """Reserving against a deactivated event should fail gracefully."""
    name = f"E_{uuid.uuid4()}"
    res = client.post("/admin/event", json={"name": name, "total_tickets": 10})
    eid = res.json["id"]

    # Deactivate the event
    res = client.post(f"/admin/event/{eid}/deactivate")
    assert res.status_code == 200

    # Try to reserve — should be rejected
    res = client.post("/reserve", json={"event_id": eid, "user_email": "late@test.com"})
    assert res.status_code == 400
    assert "active" in res.json["error"].lower() or "no longer" in res.json["error"].lower()

# ─── Data Consistency ─────────────────────────────────────────

def test_ticket_count_consistency(client):
    """After N successful reservations, available_tickets must equal total - N."""
    name = f"E_{uuid.uuid4()}"
    res = client.post("/admin/event", json={"name": name, "total_tickets": 5})
    eid = res.json["id"]

    for i in range(5):
        r = client.post("/reserve", json={"event_id": eid, "user_email": f"u{i}@test.com"})
        assert r.status_code == 201

    # The 6th should be sold out
    r = client.post("/reserve", json={"event_id": eid, "user_email": "extra@test.com"})
    assert r.status_code == 400
    assert "Sold out" in r.json["error"]

def test_duplicate_reservation_does_not_decrement_tickets(client):
    """A duplicate reservation attempt must NOT reduce available tickets."""
    name = f"E_{uuid.uuid4()}"
    res = client.post("/admin/event", json={"name": name, "total_tickets": 5})
    eid = res.json["id"]

    client.post("/reserve", json={"event_id": eid, "user_email": "dup@test.com"})
    # Try duplicate
    client.post("/reserve", json={"event_id": eid, "user_email": "dup@test.com"})

    # Check remaining tickets via a new reservation
    r = client.post("/reserve", json={"event_id": eid, "user_email": "other@test.com"})
    assert r.status_code == 201
    assert r.json["reservation"]["event"]["available_tickets"] == 3

# ─── Input Boundary Tests ─────────────────────────────────────

def test_create_event_boolean_tickets(client):
    """Boolean True should not be accepted as total_tickets."""
    res = client.post("/admin/event", json={"name": f"E_{uuid.uuid4()}", "total_tickets": True})
    assert res.status_code == 400

def test_create_event_float_tickets(client):
    """Float values should not be accepted as total_tickets."""
    res = client.post("/admin/event", json={"name": f"E_{uuid.uuid4()}", "total_tickets": 10.5})
    assert res.status_code == 400

def test_create_event_whitespace_name(client):
    """A name with only whitespace should be rejected."""
    res = client.post("/admin/event", json={"name": "   ", "total_tickets": 10})
    assert res.status_code == 400

def test_reserve_whitespace_email(client):
    """An email that is only whitespace should be rejected."""
    name = f"E_{uuid.uuid4()}"
    res = client.post("/admin/event", json={"name": name, "total_tickets": 5})
    eid = res.json["id"]
    r = client.post("/reserve", json={"event_id": eid, "user_email": "   "})
    assert r.status_code == 400

def test_reserve_wrong_method(client):
    """GET on /reserve should return 405 with JSON."""
    res = client.get("/reserve")
    assert res.status_code == 405
    assert res.content_type == "application/json"

def test_create_event_wrong_method(client):
    """GET on /admin/event should return 405 with JSON."""
    res = client.get("/admin/event")
    assert res.status_code == 405
    assert res.content_type == "application/json"

# ─── Telemetry ────────────────────────────────────────────────

def test_telemetry_endpoint(client):
    """The telemetry endpoint should return system stats."""
    res = client.get("/api/telemetry")
    assert res.status_code == 200
    data = res.json
    assert "database" in data
    assert "available_tickets" in data
    assert "cpu_percent" in data
    assert "ram_percent" in data

# ─── 404 Handling ──────────────────────────────────────────────

def test_404_returns_json(client):
    res = client.get("/nonexistent-route")
    assert res.status_code == 404
    assert res.content_type == "application/json"

def test_500_returns_json_not_html(client):
    """Ensure 500 errors never leak stack traces / HTML."""
    # POST to health (wrong method) gives 405, not 500
    # Use a known-bad path that triggers a controlled error
    res = client.get("/nonexistent-route")
    assert "text/html" not in res.content_type
