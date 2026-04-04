# Flash Sale Reservation API Implementation Plan

This plan maps out our approach to building a "Flash Sale" Ticket Reservation system. The goal is to build a robust API that handles massive bursts of traffic without "overselling" inventory, demonstrating strong Production Engineering (PE) principles like database concurrency and race condition mitigation.

## Overview

We will create an API where users can reserve a ticket for a high-demand event. We'll start with a naive implementation (Bronze), prove it fails under concurrent load, and then implement robust locking to fix it (Silver).

## Milestones

### 1. Bronze Tier: The Naive Implementation
We need to get the core application running securely under standard Flask development practices. We will build the basic CRUD without worrying about concurrency yet.

#### Models (`app/models/flash_sale.py`)
* **`Event`:** Model tracking the sale. Fields: `name` (String), `total_tickets` (Integer), `available_tickets` (Integer).
* **`Reservation`:** Model tracking a success. Fields: `event_id` (ForeignKey), `user_email` (String).

#### Routes (`app/routes/reservations.py`)
* `POST /admin/event`: Creates a new flash sale event with a set number of tickets.
* `POST /reserve`: Basic endpoint that takes `{"event_id": 1, "user_email": "test@test.com"}`.
  - *Naive Logic:* Reads `available_tickets`. If `> 0`, subtracts 1, saves the event, and creates a `Reservation`.

#### CI/CD Setup (GitHub Actions)
* Before touching complex locking logic, we will configure `pytest` locally.
* Create `.github/workflows/ci.yml` to run our test suite, ensuring our basic routing works. This will prove we have a robust pipeline ready *before* we start making dangerous concurrency changes.

### 2. Silver Tier: The Reliability Upgrade
We will purposefully load-test our Bronze API using a script to simulate 100 concurrent requests. Due to race conditions, the Bronze API will accidentally "oversell" tickets (e.g., selling 105 tickets when only 100 existed). We will then fix it.

#### Refactoring /reserve
* Upgrade the endpoint to use **Row-level pessimistic locking** (`SELECT ... FOR UPDATE` via Peewee `for_update()`) inside a `db.atomic()` transaction.
* Alternatively, use **Atomic Updates** (`UPDATE Event SET available_tickets = available_tickets - 1 WHERE available_tickets > 0`).
* Re-run the load test to mathematically prove the API reliably stops at exactly 0 tickets, no matter the load.

### 3. Gold Tier: Production Polish
* Ensure `pytest` tests cover both success and "sold out" failure cases gracefully.
* Implement structured JSON error handlers (no messy HTML stack traces).
* Ship a `docker-compose.yml` to package both the Flask API (using a production `gunicorn` server) and PostgreSQL.

## User Review Required
> [!IMPORTANT]
> Since we pivoted from the URL shortener, our code paths will change entirely. I'll scaffold the `Event` and `Reservation` models and clear out the old URL shortener placeholders from our markdown docs. 

## Proposed File Changes

#### [NEW] app/models/flash_sale.py
Will contain the `Event` and `Reservation` models leveraging our `BaseModel`.

#### [MODIFY] app/models/__init__.py
Expose the models for Peewee table generation.

#### [NEW] app/routes/reservations.py
Flask blueprint holding `POST /admin/event` and `POST /reserve`.

#### [MODIFY] app/routes/__init__.py
Register the new blueprint.

#### [MODIFY] app/database.py
Add a hook to ensure `Event` and `Reservation` tables auto-generate when you run the app locally.

## Verification Plan
1. **Sanity Check:** Start the API and manually create an Event via `curl`. Manual validation of `/reserve`.
2. **Concurrency Test:** We will write a small python multithreading script (or use `k6`) to bombard the API and verify how it behaves under load.
