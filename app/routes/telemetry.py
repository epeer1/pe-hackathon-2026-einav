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

    return jsonify({
        "database": db_status,
        "available_tickets": available_tickets,
        "cpu_percent": cpu_percent,
        "ram_percent": ram_info.percent,
        # Displaying genuine 1:1 topology mapping for our local cluster
        "be_instances": 1, 
        "db_instances": 1
    }), 200
