# Flash Sale Reservation API

> **MLH Production Engineering Hackathon 2026 — Reliability Engineering Quest**
>
> A high-concurrency ticket reservation system that refuses to die under load. Handles thousands of simultaneous users without overselling a single ticket.

**GitHub:** [epeer1/pe-hackathon-2026-einav](https://github.com/epeer1/pe-hackathon-2026-einav)
**Demo Video:** _[link]_

---

## Tech Stack

Flask · Peewee ORM · PostgreSQL · Gunicorn · Docker Compose · React + Vite

---

## Quick Start

```bash
git clone https://github.com/epeer1/pe-hackathon-2026-einav.git
cd pe-hackathon-2026-einav
docker compose up --build
```

| Service   | URL                          |
|-----------|------------------------------|
| API       | http://localhost:5050         |
| Dashboard | http://localhost:5173         |
| Health    | http://localhost:5050/health  |

All three containers (API, DB, Frontend) start automatically. No manual setup needed.

---

## How It Works

### Core Flow

1. **Create an event** — `POST /admin/event` with a name and ticket count.
2. **Reserve tickets** — `POST /reserve` with an event ID and user email. Each user can reserve once per event.
3. **Sell out safely** — Under any concurrent load, exactly `total_tickets` reservations succeed. Zero overselling.

### Concurrency Control

The reservation endpoint uses **pessimistic row-level locking** to prevent overselling:

```
POST /reserve
  → BEGIN transaction
  → SELECT ... FOR UPDATE  (locks the event row)
  → Decrement available_tickets
  → INSERT reservation (unique constraint: user + event)
  → COMMIT
```

If two users hit the same ticket simultaneously, one locks the row and succeeds; the other waits for the lock, then sees the updated count. If a duplicate reservation is attempted, the ticket decrement is rolled back inside a nested savepoint — the count stays correct.

### Input Validation

Every request is validated before touching the database:

- Missing or empty fields → `400`
- Boolean/float passed as integer → `400`
- Whitespace-only name or email → `400`
- Email without `@` → `400`
- String or boolean as `event_id` → `400`
- Non-JSON content types → `400`

### Error Handling

All errors return JSON. No HTML stack traces ever reach the client.

| Code  | Meaning                    |
|-------|----------------------------|
| `400` | Bad input, sold out, inactive event |
| `404` | Event or route not found   |
| `405` | Wrong HTTP method          |
| `409` | Duplicate reservation      |
| `413` | Payload too large (>1MB)   |
| `429` | Rate limit exceeded        |
| `500` | Internal error (details logged server-side only) |

### Security

- **Rate limiting** — Flask-Limiter with per-IP limits (strict on `/api/ping`, exempted on high-throughput routes for load testing)
- **Security headers** — `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`, `Cache-Control: no-store`
- **Request size limit** — 1MB max via `MAX_CONTENT_LENGTH`
- **ORM parameterization** — Peewee prevents SQL injection by default

### Auto-Recovery (Chaos Mode)

All Docker containers run with `restart: always`. PostgreSQL data is stored on a named Docker volume (`pgdata`).

- **Kill the API** → Docker respawns Gunicorn in ~1 second. Mid-flight transactions roll back cleanly via PostgreSQL.
- **Kill the database** → PostgreSQL restarts with all data intact (volume-backed). API returns `500` JSON during the gap, then reconnects automatically.
- **Kill the frontend** → Restarts independently; API continues serving.
- **Crash recovery test** — pytest verifies events and reservations survive a full app restart.

Full failure mode documentation: [docs/failure_manual.md](docs/failure_manual.md)

### Dynamic Autoscaling

Gunicorn workers scale from 1 to 6 based on real-time requests per second:
- **Worker class:** `gthread` — each worker handles 4 concurrent requests via threads, avoiding blocking under load
- Scale **up** when RPS/worker > 20 (via `SIGTTIN`)
- Scale **down** when RPS/worker < 5 (via `SIGTTOU`)
- 3-second check interval, 6-second cooldown between scaling events

---

## API Reference

| Method | Endpoint                         | Description              |
|--------|----------------------------------|--------------------------|
| `GET`  | `/health`                        | Health check             |
| `POST` | `/admin/event`                   | Create a flash sale      |
| `POST` | `/admin/event/<id>/deactivate`   | Deactivate an event      |
| `POST` | `/reserve`                       | Reserve a ticket         |
| `GET`  | `/api/telemetry`                 | System stats (CPU, RAM, workers, RPS) |
| `GET`  | `/api/logs`                      | Recent error log entries |

### Examples

```bash
# Create event
curl -X POST http://localhost:5050/admin/event \
  -H "Content-Type: application/json" \
  -d '{"name": "FlashSale", "total_tickets": 100}'

# Reserve ticket
curl -X POST http://localhost:5050/reserve \
  -H "Content-Type: application/json" \
  -d '{"event_id": 1, "user_email": "user@example.com"}'

# Deactivate event
curl -X POST http://localhost:5050/admin/event/1/deactivate
```

---

## Testing

```bash
# Run tests with coverage
docker compose exec api uv run python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

**38 tests · 92% coverage** — health check, full reservation flow, sold out, duplicate user, inactive event, deactivation of nonexistent events, bad input types (boolean, float, string, whitespace, null), HTTP method enforcement, data consistency verification, error log integration, no-detail-leak validation, and crash recovery with data persistence.

### Load Test

```bash
python load_test.py -t 5000 -u 8000 -w 200
```

Spins up 200 threads sending 8000 reservation requests for 5000 tickets. Verifies exactly 5000 sell, 3000 are rejected, zero oversold. Built-in retry logic survives mid-test container crashes.

---

## Dashboard

The React frontend at `http://localhost:5173` provides real-time operations visibility:

- **System telemetry** — database status, CPU/RAM, active Gunicorn worker count, requests per second
- **Traffic chart** — canvas-rendered rolling 60-second RPS view with EMA smoothing
- **Flash sale controls** — create events with configurable ticket counts
- **Load simulator** — trigger concurrent user bursts and watch tickets drain live
- **Error log feed** — color-coded recent errors pulled from the database

---

## CI/CD

GitHub Actions runs on every push and PR to `master`:

1. Spins up a PostgreSQL 15 service container
2. Installs dependencies via `uv sync`
3. Runs `pytest --cov-fail-under=70`

If tests fail or coverage drops below 70%, the pipeline blocks the commit.

---

## Project Structure

```
├── app/
│   ├── __init__.py              # App factory, middleware, error handlers
│   ├── database.py              # Peewee DB proxy, connection lifecycle
│   ├── error_log.py             # DB-backed error logging
│   ├── models/flash_sale.py     # Event + Reservation models
│   └── routes/
│       ├── reservations.py      # /admin/event, /reserve, /deactivate
│       └── telemetry.py         # /api/telemetry, shared RPS counter
├── frontend/                    # React + Vite dashboard
├── tests/test_api.py            # 38 tests, 92% coverage
├── docs/
│   ├── quest_requirements.md    # Bronze/Silver/Gold checklist
│   └── failure_manual.md        # Failure mode documentation
├── docker-compose.yml           # API + DB + Frontend (3 containers)
├── Dockerfile                   # Python API image
├── gunicorn.conf.py             # gthread workers, autoscaler (1-6)
├── load_test.py                 # Concurrency stress test
└── .github/workflows/ci.yml    # CI pipeline with coverage gate
```

---

## Quest Completion

| Tier | Requirement | Status |
|------|-------------|--------|
| 🥉 Bronze | Unit tests with pytest | ✅ 38 tests passing |
| 🥉 Bronze | CI via GitHub Actions | ✅ Runs on every push |
| 🥉 Bronze | `/health` endpoint | ✅ Returns `{"status": "ok"}` |
| 🥈 Silver | ≥50% code coverage | ✅ 92% |
| 🥈 Silver | Integration tests | ✅ Full API flow tests |
| 🥈 Silver | CI blocks bad deploys | ✅ `--cov-fail-under=70` |
| 🥈 Silver | Error handling docs | ✅ [failure_manual.md](docs/failure_manual.md) |
| 🥇 Gold | ≥70% code coverage | ✅ 92% |
| 🥇 Gold | Graceful failure (JSON errors) | ✅ 400/404/405/409/413/429/500 |
| 🥇 Gold | Chaos mode (auto-restart) | ✅ `restart: always` + persistent volume |
| 🥇 Gold | Failure manual | ✅ [failure_manual.md](docs/failure_manual.md) |
