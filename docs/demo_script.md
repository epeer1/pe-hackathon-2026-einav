# Demo Video Script (2 minutes, no voice — text overlays only)

**Format:** Screen recording with bold text overlays between scenes. Target 1:50.
**Recording:** QuickTime (built-in macOS) or OBS. Add text overlays in iMovie after recording raw footage.
**Prep:** Increase Terminal font to 16pt+ (Terminal > Settings > Profiles > Text). Clean desktop, no notifications.

---

## Scene 1 — Title Card (0:00–0:05)

**Screen:** Black screen + white text (add in video editor, nothing to record)

**Text overlay (centered, large):**
> **Flash Sale Reservation API**
> Reliability Engineering Quest — MLH PE Hackathon 2026

---

## Scene 2 — One Command Deploy (0:05–0:15)

**Screen:** Terminal only (full screen)

**Text overlay:** `One command. Three containers. Zero config.`

**Action:**
- Type `docker compose up --build` (fast-forward the build)
- Run `docker compose ps` — show all 3 containers healthy

---

## Scene 3 — Dashboard (0:15–0:30)

**Screen:** Browser only (full screen) — `http://localhost:5173`

**Text overlay:** `Real-time SRE Dashboard`

**Action:**
- Slowly mouse over each section:
  - DB status: green "ONLINE"
  - CPU / RAM gauges
  - Gunicorn worker count
  - Live RPS chart (flat line — no traffic yet)

---

## Scene 4 — Load Test (0:30–0:55)

**Screen:** Split — browser left half, terminal right half

**Text overlay:** `200 users. 100 tickets. Zero oversold.`

**Action:**
1. Terminal (right): run `uv run python load_test.py -t 100 -u 200 -w 100`
2. Dashboard (left): watch the RPS chart spike and tickets drain to 0
3. Terminal shows: **"✅ PASS: API maintained integrity under load. 100 sold, 100 blocked"**

**Text overlay (after result):** `SELECT ... FOR UPDATE — pessimistic row-level locking`

---

## Scene 5 — Chaos: Kill the API (0:55–1:15)

**Screen:** Split — browser left half, terminal right half
*(Resize manually or use Rectangle app before recording)*

**Text overlay:** `Chaos Mode: Kill the API container`

**Action:**
1. Terminal (right): type `docker kill pe-hackathon-2026-einav-api-1`
2. Dashboard (left): status indicators go red/offline, RPS drops to 0
3. Terminal (right): type `docker compose up -d` (one-command recovery)
4. Dashboard (left): status recovers to green within seconds

**Text overlay (after recovery):** `Container killed → one command → fully recovered`

---

## Scene 6 — Graceful Error Handling (1:15–1:30)

**Screen:** Terminal only (full screen)

**Text overlay:** `Bad input → clean JSON. Never a stack trace.`

**Action (run these 3 commands, quick cuts between them):**

```bash
# Invalid event_id type → 400
curl -s -X POST http://localhost:5050/reserve \
  -H "Content-Type: application/json" \
  -d '{"event_id": "abc", "user_email": "x@test.com"}' | python3 -m json.tool
```

```bash
# Unknown route → 404
curl -s http://localhost:5050/doesnt-exist | python3 -m json.tool
```

```bash
# Wrong HTTP method → 405
curl -s -X GET http://localhost:5050/reserve | python3 -m json.tool
```

**Text overlay:** `400 · 404 · 405 · 409 · 413 · 429 · 500 — all JSON`

---

## Scene 7 — Tests + Coverage (1:30–1:45)

**Screen:** Terminal only (full screen) → then quick cut to browser (GitHub)

**Text overlay:** `38 tests · 92% coverage · CI gated`

**Action:**
- Terminal: run `uv run python -m pytest tests/ -v --cov=app` (fast-forward)
- Pause on the final line: **38 passed, 92%**
- Quick cut to browser: GitHub Actions page — green checkmark on latest commit

**Text overlay:** `CI blocks any push below 70% coverage`

---

## Scene 8 — Closing Card (1:45–1:50)

**Screen:** Black screen + white text (add in video editor, nothing to record)

**Text overlay (centered, large):**
> **Gold Tier Complete**
>
> 38 tests · 92% coverage · Chaos recovery · Graceful errors
> Zero overselling under 8000 concurrent requests
>
> github.com/epeer1/pe-hackathon-2026-einav

---

## Recording Checklist

- [ ] Colima running (`colima status`)
- [ ] Docker containers up: `docker compose up -d` — all 3 healthy
- [ ] Dashboard open in browser at `http://localhost:5173`
- [ ] API responding: `curl http://localhost:5050/health`
- [ ] Terminal font size 16pt+
- [ ] Clean desktop, Do Not Disturb mode on
- [ ] Rectangle app ready for split screen (Scene 4 & 5)
- [ ] Fast-forward `docker compose up --build` and `pytest` in editor
- [ ] Cut between scenes — no dead air
- [ ] Add text overlays in iMovie after recording
- [ ] Total time under 2:00
- [ ] Export at 1080p minimum
