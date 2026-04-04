# Flash Sale Failure Manual

This document maps out the specific failure domains for our high-concurrency reservation API and exactly how the application handles them without crashing.

## Graceful HTTP Error Handling

To satisfy Production Engineering routing rules, this application restricts untyped/unformatted Python stack traces. All upstream users will receive strict JSON payloads allowing their frontends to decay gracefully.

### 404: Resource Not Found
If an upstream client accesses an invalid route or requests an event that doesn't exist in the database (e.g., `POST /reserve` with a phantom `event_id`), the application aborts immediately and returns:
```json
HTTP 404
{
  "error": "Resource not found" 
}
```
*(Specific validation errors will return `Event not found`).*

### 400: Invalid Input or Logical Rejection
If a client submits bad POST data, violates a database integrity constraint (like trying to create an Event name that already exists), or tries to reserve an event with `available_tickets = 0`, the system rejects the transaction safely:
```json
HTTP 400
{
  "error": "Sold out" 
}
```

### 500: Database Disconnection or Syntax Failure
If PostgreSQL drops the connection, an unexpected locking error occurs, or buggy Python code is shipped, the `@app.errorhandler(Exception)` catches it at the highest factory runtime level. Instead of disconnecting or dropping into HTML debugger mode, the API returns:
```json
HTTP 500
{
  "error": "Unexpected failure",
  "details": "<str(exc)>"
}
```

## Chaos Mode & Component Failures

### 1. PostgreSQL Container Failure (`docker kill`)
If the `db` container experiences an Out-Of-Memory (OOM) kill or is explicitly terminated via Chaos Engineering test, two things happen:
1. Because `docker-compose.yml` configures `restart: unless-stopped`, Docker's daemon immediately spawns a new PostgreSQL instance.
2. In the resulting downtime window (typically 3-5 seconds), the Flask container cleanly processes the lost connection and wraps the `OperationalError` via our global `500` handler, returning `{ "error": "Unexpected failure" }` to the client instead of hanging the HTTP socket indefinitely. Once Postgres resurrects, Peewee automatically re-establishes the pool.

### 2. API Container Failure
If the `api` node dies, Gunicorn and Docker natively restart it via the composed `restart: unless-stopped` policy. Any mid-flight reservations locked in the database via `db.atomic()` are forcefully rolled back by PostgreSQL upon socket termination, preserving data consistency and preventing "ghost tickets" from being reserved.
