# Flash Sale Failure Manual

This document maps out the specific failure domains for our high-concurrency reservation API and exactly how the application handles them without crashing.

---

## Graceful HTTP Error Handling

All errors return strict JSON payloads — no HTML stack traces ever reach the client, allowing frontends to degrade gracefully.

### 400: Invalid Input or Logical Rejection
Bad POST data, integrity constraint violations (duplicate event name), sold-out events, or inactive events.
```json
{"error": "Sold out"}
```

### 404: Resource Not Found
Invalid route or nonexistent event/resource.
```json
{"error": "Event not found"}
```

### 405: Method Not Allowed
Wrong HTTP method on a valid route (e.g., `GET /reserve`).
```json
{"error": "Method not allowed"}
```

### 409: Conflict
Duplicate reservation (same user + same event).
```json
{"error": "User already has a reservation for this event"}
```

### 413: Payload Too Large
Request body exceeds 1MB limit.
```json
{"error": "Payload too large (max 1MB)"}
```

### 429: Rate Limit Exceeded
Per-IP rate limit exceeded (200/min default).
```json
{"error": "Rate limit exceeded"}
```

### 500: Internal Server Error
Database disconnection, unexpected locking error, or unhandled exception. The detail is logged server-side only — never exposed to the client.
```json
{"error": "Internal server error"}
```

---

## Chaos Mode & Component Failures

### 1. PostgreSQL Container Failure

**What happens:** The `db` container is killed via `docker kill`, OOM, or hardware fault.

**Automatic recovery:**
1. Docker's `restart: always` policy immediately spawns a new PostgreSQL instance.
2. Data is preserved on the `pgdata` named volume — no data loss.
3. During the ~3-5 second downtime window, API requests receive `500` JSON responses (not hangs or timeouts).
4. Once Postgres is back, Peewee's `connect(reuse_if_open=True)` re-establishes connections automatically.

**Runbook — if automatic recovery fails:**
```bash
# 1. Check container status
docker compose ps db

# 2. Check PostgreSQL logs
docker compose logs --tail=50 db

# 3. Manual restart
docker compose restart db

# 4. Verify recovery
curl http://localhost:5050/api/telemetry   # "database": "online"

# 5. If data volume is corrupted (last resort)
docker compose down -v    # WARNING: destroys all data
docker compose up -d
```

**Recovery time:** 3-5 seconds (automatic), <30 seconds (manual restart).

### 2. API Container Failure

**What happens:** The `api` container crashes, is killed, or Gunicorn dies.

**Automatic recovery:**
1. Docker's `restart: always` policy respawns the container immediately.
2. Gunicorn boots with `preload_app = True` and the autoscaler re-initializes at 1 worker.
3. Any mid-flight transactions locked via `db.atomic()` + `SELECT ... FOR UPDATE` are forcefully rolled back by PostgreSQL when the socket dies — no "ghost tickets" or partial reservations.

**Runbook — if automatic recovery fails:**
```bash
# 1. Check container status
docker compose ps api

# 2. Check Gunicorn/application logs
docker compose logs --tail=50 api

# 3. Common causes:
#    - "worker timeout" → requests taking >30s, check DB health first
#    - "connection refused" on DB → DB container is down, fix that first
#    - OOM kill → increase container memory limit in docker-compose.yml

# 4. Manual restart
docker compose restart api

# 5. Verify recovery
curl http://localhost:5050/health   # {"status": "ok"}
```

**Recovery time:** 1-2 seconds (automatic).

### 3. Frontend Container Failure

**What happens:** The frontend Vite/Node process crashes.

**Impact:** Dashboard goes offline. API continues serving all traffic normally — the frontend is purely observational.

**Recovery:** `restart: always` respawns it. Manual: `docker compose restart frontend`.

### 4. Full Stack Failure (All Containers)

**Runbook:**
```bash
# Nuclear restart
docker compose down
docker compose up -d

# Verify all services
curl http://localhost:5050/health              # API alive
curl http://localhost:5050/api/telemetry       # DB online
curl http://localhost:5173                      # Dashboard loads
```

**Data safety:** All event and reservation data survives on the `pgdata` volume. Only `docker compose down -v` destroys it.

---

## Data Consistency Under Failure

| Scenario | Data Impact | Protection Mechanism |
|----------|------------|---------------------|
| API crash mid-reservation | Transaction rolled back, no ticket lost | PostgreSQL auto-rollback on disconnect |
| Two users reserve the same last ticket | Exactly one succeeds | `SELECT ... FOR UPDATE` row lock |
| Same user reserves twice | Second attempt rejected (409) | Unique compound index `(event, user_email)` |
| Duplicate reservation attempt | Ticket count is NOT decremented | Nested savepoint rollback restores the count |
| DB crash mid-transaction | Transaction rolled back | WAL + crash recovery |

---

## Monitoring & Observability

### Health Check
```bash
curl http://localhost:5050/health
# {"status": "ok"} → API is alive
```

### Telemetry
```bash
curl http://localhost:5050/api/telemetry
# Returns: database status, available tickets, CPU%, RAM%, worker count, RPS
```

### Error Logs
```bash
curl http://localhost:5050/api/logs
# Returns: last 50 errors with timestamp, status code, method, path
```

### Dashboard
The React frontend at `http://localhost:5173` provides real-time visibility into all of the above — database status flips to "OFFLINE" within 800ms of a container kill, and recovers visually when the service returns.

---

## Escalation

| Severity | Condition | Action |
|----------|-----------|--------|
| **Low** | Single 500 error in logs | Check `/api/logs`, likely transient DB blip |
| **Medium** | `/health` returns non-200 | Check `docker compose ps`, restart affected container |
| **High** | Database shows "offline" on dashboard | `docker compose logs db`, then `docker compose restart db` |
| **Critical** | All containers down | `docker compose down && docker compose up -d`, verify data on `pgdata` volume |
