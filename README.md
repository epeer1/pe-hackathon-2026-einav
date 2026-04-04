# Flash Sale Reservation API

A high-concurrency ticket reservation system built for the MLH Production Engineering Hackathon 2026. The API handles massive bursts of traffic without overselling inventory, backed by pessimistic row-level locking and a real-time monitoring dashboard.

**Quest:** Reliability Engineering — Build a service that refuses to die easily.

**Stack:** Flask · Peewee ORM · PostgreSQL · Gunicorn · Docker · React + Vite

---

## Quick Start

```bash
git clone https://github.com/epeer1/pe-hackathon-2026-einav.git
cd pe-hackathon-2026-einav
docker compose up --build
```

| Service | URL |
|---------|-----|
| API | http://localhost:5000 |
| Dashboard | http://localhost:5173 |
| Health Check | http://localhost:5000/health |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Returns `{"status": "ok"}` |
| `POST` | `/admin/event` | Create a flash sale event |
| `POST` | `/admin/event/<id>/deactivate` | Deactivate an event |
| `POST` | `/reserve` | Reserve a ticket for an event |
| `GET` | `/api/telemetry` | System stats (DB, CPU, RAM, workers) |

### Create an event
```bash
curl -X POST http://localhost:5000/admin/event \
  -H "Content-Type: application/json" \
  -d '{"name": "FlashSale", "total_tickets": 100}'
```

### Reserve a ticket
```bash
curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{"event_id": 1, "user_email": "user@example.com"}'
```

---

## Reliability Features

### Concurrency Protection
- `SELECT ... FOR UPDATE` pessimistic row-level locking inside `db.atomic()` transactions
- Prevents overselling under any load — verified by load test (150 concurrent users, 100 tickets, 0 oversold)

### Graceful Error Handling
Every error returns structured JSON — never HTML stack traces:
- `400` — bad input, sold out, inactive event
- `404` — event/route not found
- `405` — wrong HTTP method
- `409` — duplicate reservation
- `500` — unexpected failures caught by global handler

### Chaos Engineering
- Docker `restart: unless-stopped` on all containers
- Kill API or DB container → auto-restarts in seconds
- Mid-flight transactions roll back cleanly via PostgreSQL
- See [Failure Manual](docs/failure_manual.md) for full failure mode documentation

### CI/CD
- GitHub Actions runs `pytest` with coverage gate (≥70%) on every push
- Tests must pass before code reaches `master`

---

## Testing

```bash
# Run the full test suite inside Docker
docker compose exec api uv run python -m pytest tests/ --cov=app --cov-report=term-missing -v
```

**30 tests · 93% code coverage** covering:
- Health check, event CRUD, reservation flows
- Sold out, duplicate user, inactive event, nonexistent event
- Bad input (missing fields, invalid email, wrong types, garbage body)
- HTTP method enforcement (405 JSON)
- Data consistency (ticket counts, rollback on duplicate)

### Load Test
```bash
python load_test.py
```
Spins up 150 concurrent users fighting for 100 tickets. Verifies exactly 100 sell, 50 are blocked.

---

## Dashboard

The React frontend at http://localhost:5173 provides a real-time operations dashboard:

- **Live telemetry** — database status, CPU/RAM usage, active Gunicorn workers
- **Traffic chart** — rolling 60-second view of reservation activity
- **Launch flash sales** — create events with configurable ticket counts directly from the UI
- **Simulate load** — trigger concurrent user bursts and watch tickets drain in real time
- **Node health indicators** — visual status of API and database containers

The dashboard polls `/api/telemetry` every 800ms and reflects the system state as it changes — including during chaos tests (kill a container and watch the status flip to offline, then recover).

---

## Project Structure

```
├── app/
│   ├── __init__.py              # App factory, error handlers
│   ├── database.py              # Peewee DB proxy, connection hooks
│   ├── models/flash_sale.py     # Event + Reservation models
│   └── routes/
│       ├── reservations.py      # /admin/event, /reserve, /deactivate
│       └── telemetry.py         # /api/telemetry (system stats)
├── frontend/                    # React dashboard (Vite)
├── tests/test_api.py            # 30 tests, 93% coverage
├── docs/
│   ├── quest_requirements.md    # Bronze/Silver/Gold checklist
│   └── failure_manual.md        # Failure mode documentation
├── docker-compose.yml           # API + DB + Frontend
├── Dockerfile                   # Python API container
├── gunicorn.conf.py             # 4 workers, preload
├── load_test.py                 # Concurrency stress test
└── .github/workflows/ci.yml    # CI pipeline
```

---

## Quest Completion

| Tier | Requirement | Status |
|------|-------------|--------|
| 🥉 Bronze | Unit tests with pytest | ✅ 30 tests |
| 🥉 Bronze | CI via GitHub Actions | ✅ Runs on every push |
| 🥉 Bronze | `/health` endpoint | ✅ Returns 200 |
| 🥈 Silver | ≥50% code coverage | ✅ 93% |
| 🥈 Silver | Integration tests | ✅ Full API flow tests |
| 🥈 Silver | CI blocks bad deploys | ✅ Coverage gate ≥70% |
| 🥈 Silver | Error handling docs | ✅ failure_manual.md |
| 🥇 Gold | ≥70% code coverage | ✅ 93% |
| 🥇 Gold | Graceful failure (JSON) | ✅ All error codes |
| 🥇 Gold | Chaos mode (auto-restart) | ✅ Docker restart policy |
| 🥇 Gold | Failure manual | ✅ docs/failure_manual.md |

## Useful Peewee Patterns

```python
from peewee import fn
from playhouse.shortcuts import model_to_dict

# Select all
products = Product.select()

# Filter
cheap = Product.select().where(Product.price < 10)

# Get by ID
p = Product.get_by_id(1)

# Create
Product.create(name="Widget", category="Tools", price=9.99, stock=50)

# Convert to dict (great for JSON responses)
model_to_dict(p)

# Aggregations
avg_price = Product.select(fn.AVG(Product.price)).scalar()
total = Product.select(fn.SUM(Product.stock)).scalar()

# Group by
from peewee import fn
query = (Product
         .select(Product.category, fn.COUNT(Product.id).alias("count"))
         .group_by(Product.category))
```

## Tips

- Use `model_to_dict` from `playhouse.shortcuts` to convert model instances to dictionaries for JSON responses.
- Wrap bulk inserts in `db.atomic()` for transactional safety and performance.
- The template uses `teardown_appcontext` for connection cleanup, so connections are closed even when requests fail.
- Check `.env.example` for all available configuration options.
