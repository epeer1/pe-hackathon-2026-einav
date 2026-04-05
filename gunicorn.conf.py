import os
import signal
import threading
import time

bind = "0.0.0.0:5050"
workers = 1  # Start lean, autoscaler will add more
worker_class = "gthread"
threads = 4  # Each worker handles 4 concurrent requests
timeout = 30
preload_app = True

# ── Dynamic Autoscaler ─────────────────────────────
MIN_WORKERS = 1
MAX_WORKERS = 6
SCALE_UP_RPS = 20       # Scale up when rps exceeds this per worker
SCALE_DOWN_RPS = 5       # Scale down when rps drops below this per worker
CHECK_INTERVAL = 3       # Seconds between checks
COOLDOWN = 6             # Seconds after a scale event before next


def when_ready(server):
    """Runs in the Gunicorn master process once the server is ready."""
    def autoscaler():
        last_scale_time = 0
        last_req_count = None
        last_check_time = None

        while True:
            time.sleep(CHECK_INTERVAL)
            now = time.monotonic()

            # Read request counter from shared multiprocessing value
            try:
                from app.routes.telemetry import _req_count
                with _req_count.get_lock():
                    current_count = _req_count.value
            except Exception:
                continue

            if last_req_count is None or last_check_time is None:
                last_req_count = current_count
                last_check_time = now
                continue

            elapsed = now - last_check_time
            if elapsed < 1:
                continue

            rps = (current_count - last_req_count) / elapsed
            last_req_count = current_count
            last_check_time = now

            num_workers = len(server.WORKERS)
            rps_per_worker = rps / max(num_workers, 1)

            # Cooldown check
            if (now - last_scale_time) < COOLDOWN:
                continue

            if rps_per_worker > SCALE_UP_RPS and num_workers < MAX_WORKERS:
                os.kill(server.pid, signal.SIGTTIN)
                last_scale_time = now
                server.log.info(f"[autoscaler] Scaling UP to {num_workers + 1} workers (rps={rps:.0f})")
            elif rps_per_worker < SCALE_DOWN_RPS and num_workers > MIN_WORKERS:
                os.kill(server.pid, signal.SIGTTOU)
                last_scale_time = now
                server.log.info(f"[autoscaler] Scaling DOWN to {num_workers - 1} workers (rps={rps:.0f})")

    t = threading.Thread(target=autoscaler, daemon=True)
    t.start()
    server.log.info("[autoscaler] Started with 1 worker, will scale 1-6 based on load")
