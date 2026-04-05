import time
import threading
import multiprocessing
import psutil
from flask import Blueprint, jsonify
from app.database import db
from app.models.flash_sale import Event

telemetry_bp = Blueprint("telemetry", __name__)

# Shared counter across all forked workers + master (created before fork due to preload_app)
_req_count = multiprocessing.Value('i', 0)
_rps_lock = threading.Lock()
_last_rps_time = time.monotonic()
_last_rps_count = 0
_current_rps = 0.0


def bump_request_counter():
    """Called from after_request hook to count every request."""
    with _req_count.get_lock():
        _req_count.value += 1

@telemetry_bp.route("/api/telemetry", methods=["GET"])
def get_telemetry():
    # Rate limit exempt via blueprint — high-frequency dashboard polling
    # 1. Check DB Health safely
    db_status = "offline"
    try:
        db.execute_sql('SELECT 1')
        db_status = "online"
    except Exception:
        db_status = "offline"
        
    # 2. Get Available Tickets (Gracefully handling empty DB)
    available_tickets = 0
    try:
        # Select the latest flash sale event
        event = Event.select().order_by(Event.id.desc()).get()
        available_tickets = event.available_tickets
    except Exception:
        pass 

    # 3. System Vitals
    cpu_percent = psutil.cpu_percent(interval=0)
    ram_info = psutil.virtual_memory()

    # 4. Dynamic Cluster Topology — count actual Gunicorn worker processes
    be_instances = 1
    try:
        import os
        master_pid = os.getppid()
        master = psutil.Process(master_pid)
        children = master.children(recursive=False)
        # Count only live worker children (exclude master itself)
        be_instances = max(len(children), 1)
    except Exception:
        pass

    return jsonify({
        "database": db_status,
        "available_tickets": available_tickets,
        "cpu_percent": cpu_percent,
        "ram_percent": ram_info.percent,
        "be_instances": be_instances, 
        "db_instances": 1,
        "rps": round(_compute_rps(), 1)
    }), 200


def _compute_rps():
    global _last_rps_time, _last_rps_count, _current_rps
    with _rps_lock:
        now = time.monotonic()
        elapsed = now - _last_rps_time
        if elapsed >= 0.3:
            with _req_count.get_lock():
                current = _req_count.value
            delta = current - _last_rps_count
            _last_rps_count = current
            _current_rps = delta / elapsed
            _last_rps_time = now
        return _current_rps
