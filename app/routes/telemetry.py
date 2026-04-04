import psutil
from flask import Blueprint, jsonify
from app.database import db
from app.models.flash_sale import Event

telemetry_bp = Blueprint("telemetry", __name__)

@telemetry_bp.route("/api/telemetry", methods=["GET"])
def get_telemetry():
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

    # 4. Dynamic Cluster Topology — detect real Gunicorn worker processes
    be_instances = 1  # Default for Flask dev server
    try:
        gunicorn_workers = [p for p in psutil.process_iter(['name', 'cmdline'])
                           if 'gunicorn' in (p.info.get('name') or '').lower()
                           or any('gunicorn' in arg for arg in (p.info.get('cmdline') or []))]
        if gunicorn_workers:
            be_instances = len(gunicorn_workers) - 1  # subtract the master process
            be_instances = max(be_instances, 1)
    except Exception:
        pass

    return jsonify({
        "database": db_status,
        "available_tickets": available_tickets,
        "cpu_percent": cpu_percent,
        "ram_percent": ram_info.percent,
        "be_instances": be_instances, 
        "db_instances": 1
    }), 200
