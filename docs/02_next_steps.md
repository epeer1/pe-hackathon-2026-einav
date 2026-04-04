# Next Steps & Action Plan

## Goal for the Next 30–60 Minutes
Achieve a completely functional local environment with the starter running successfully, verify the `/health` endpoint, define our DB models, and solidify our repository structure so we are ready to build "Bronze" functionality immediately.

## Exact Next Commands to Run
```bash
cd pe-hackathon-2026-einav
# We have already cloned the repository and it sits cleanly in our workspace.
# We will wipe the old git history to own the repository:
rm -rf .git
git init
git add .
git commit -m "chore: initial import of MLH pe-hackathon template"

# Setup environment config
cp .env.example .env

# Start postgres in Docker (requires Docker Desktop to be running)
docker run --name hackathon-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=hackathon_db -p 5432:5432 -d postgres:15

# Install python dependencies via uv
uv sync

# Start the application
uv run run.py

# In another terminal, verify the application boots
curl http://localhost:5000/health
```

## Environment Setup Checklist
- [x] Clone repository locally
- [ ] Initialize new `.git` repository and set local `main` branch
- [x] Create `.env` based off `.env.example`
- [ ] Ensure Postgres is running and network reachable on `localhost:5432` *(Note: Blocked due to missing docker/postgres natively)*
- [ ] Ensure `hackathon_db` is created and configured
- [x] Install dependencies with `uv sync`
- [x] Verify server starts cleanly without errors (Verified `uv run run.py` works)
- [ ] Curl `/health` endpoint returns `{"status":"ok"}` (Verified it currently returns 500 because DB isn't running)

## Repo Hygiene Checklist
- [ ] Create a local branch based on our strategy `feature/bronze-setup`
- [ ] Add `.vscode/` or local IDE settings to `.gitignore`
- [ ] Create an initial `docker-compose.yml` to track our Dockerized DB setup locally, eliminating manual `docker run` commands

## Bronze-first Plan
1. Stand up the primary Database model (`URL` or `Link`).
2. Build the `POST /shorten` endpoint to take a long URL, insert it into Postgres, and return a short token (e.g. hashids).
3. Build the `GET /<short_id>` endpoint to handle redirection (302) to the original URL.
4. Verify the database saves data and serves redirects.

## Reliability-first Plan
1. We must assume things will fail on Devpost submission day when tests and load hit the app.
2. We must enforce environment validation: Crash early if the DB is missing or `DATABASE_URL` is malformed, instead of dying upon the first user request.
3. Keep `peewee` models thin, push heavy lifting or retry logic to service wrappers if necessary.

## Shortlist First Reliability Tasks
- **pytest setup:** Add `pytest` securely via `uv add --dev pytest` and run a dummy test to ensure it runs.
- **first unit tests:** Write a basic test asserting the Flask application initializes properly without failure and returns `200 OK` on `/health`.
- **GitHub Actions CI:** Add a `.github/workflows/ci.yml` that runs `pytest` and verifies code quality when pushed.
- **graceful error responses:** Write a global, generic Flask `errorhandler` to ensure errors (e.g. 404 or 500) trigger a consistent JSON payload instead of an HTML crash page.
- **failure mode notes:** Investigate how Peewee handles dropped downstream connections (e.g., does it auto-reconnect or raise `OperationalError`?).

## Questions We Still Need Answered
- Does Peewee's default pool handle concurrency properly or do we need `playhouse.pool`?
- Will the Devpost submission mandate raw Postgres credentials or just a `DATABASE_URL`?
- Are we allowed to change ORMs if Peewee proves frustrating under pressure, or are we penalized for straying from the template stack?

## Demo Evidence We Should Collect As We Go
- Record screencasts of successful terminal CI runs (`pytest` passing).
- Take screenshots demonstrating graceful failure (sending a garbage payload and returning a 400 JSON instead of a 500 HTML trace).
- Add notes to the README describing the reliability features we prioritized.

## End-of-Day Target
By the end of today (Friday night), our primary focus:
- Working URL shortening locally up and running.
- A functional `pytest` suite testing `/health` and `/shorten`.
- `main` branch deployed to GitHub Actions with a green checkmark.
- A firm stop to rest before heavy feature development on Saturday.
