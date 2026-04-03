# Template Repository Overview

## Official Template Repo URL
[https://github.com/MLH-Fellowship/PE-Hackathon-Template-2026](https://github.com/MLH-Fellowship/PE-Hackathon-Template-2026)

## Repo Purpose
This repository provides the scaffolding for a minimal hackathon startup. It gives the basic boilerplate to build a Flask REST API connected to a PostgreSQL database with out-of-the-box data persistence, rather than forcing teams to spend hours on initial project setup.

## Tech Stack
- **Web Framework:** Flask
- **ORM:** Peewee
- **Database:** PostgreSQL
- **Package Manager:** `uv` (a fast Python package installer and environment manager)

## Local Prerequisites
- `uv` installed locally (e.g., via `curl -LsSf https://astral.sh/uv/install.sh | sh` or via homebrew)
- A local PostgreSQL server running (either natively or via Docker)

## High-Level File Tree
```
app/
├── __init__.py          # App factory and DB init
├── database.py          # Peewee DB wrapper and connection pooling
├── models/              # Models module (currently empty __init__.py)
└── routes/              # Routes module (currently empty __init__.py)
.env.example             # Template for local environment vars
pyproject.toml           # Defines project dependencies
run.py                   # Main entrypoint to start Flask server
README.md                # Hackathon instructions
```

## What the Template Already Provides
- A configured Flask Application Factory (`create_app` in `app/__init__.py`).
- Automatic database connection and teardown logic (`teardown_appcontext`).
- `pyproject.toml` with dependencies mapped (`faker`, `flask`, `peewee`, `psycopg2-binary`, `python-dotenv`).
- A `/health` route returning `{"status": "ok"}` to verify the server is running.
- Boilerplate database abstractions (`database.py` with `BaseModel`).

## What Still Must Be Implemented by Participants
- **Models:** We need to define data objects representing our domain logic.
- **Routes:** We must build the URL shortener endpoints (`POST /shorten`, `GET /<id>`).
- **CSV Data Loading:** The README mentions we have to implement logic to load CSV data.
- **Reliability Features:** Unit tests, CI/CD, handling rate-limits, validation.

## Local Run / Setup Notes
1. Setup DB credentials in `.env` (copied from `.env.example`).
2. Have PostgreSQL running locally with database `hackathon_db` created limitlessly (e.g., `createdb hackathon_db`).
3. Run `uv sync` to install dependencies into an automated `.venv`.
4. Run `uv run run.py` to start the local development server.

## Risks / Missing Pieces
- No test suite (`pytest`) is configured currently.
- No Dockerfile or `docker-compose.yml` is provided for the app or Postgres. This must be written from scratch if we want containerized deploys.
- No CI/CD pipelines (e.g., GitHub Actions) are defined in `.github/`.

## Suggested Ownership Strategy for Our Copy
Since we already cloned the repository and must submit our own public repo, we should extract the `.git` directory and re-initialize it to cut ties with the template's upstream history, making it a fresh canonical repository on our GitHub profile to comply cleanly with submission requirements.
