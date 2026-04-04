from flask import Blueprint, request, jsonify
from playhouse.shortcuts import model_to_dict
from peewee import IntegrityError
from app.models.flash_sale import Event, Reservation

reservations_bp = Blueprint("reservations", __name__)

@reservations_bp.route("/admin/event", methods=["POST"])
def create_event():
    data = request.json
    try:
        event = Event.create(
            name=data["name"],
            total_tickets=data["total_tickets"],
            available_tickets=data["total_tickets"]
        )
        return jsonify(model_to_dict(event)), 201
    except IntegrityError:
        return jsonify({"error": "Event already exists"}), 400

@reservations_bp.route("/reserve", methods=["POST"])
def reserve():
    data = request.json
    event_id = data.get("event_id")
    user_email = data.get("user_email")

    if not event_id or not user_email:
        return jsonify({"error": "Missing event_id or user_email"}), 400

    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        return jsonify({"error": "Event not found"}), 404

    # Naive concurrency logic (Bronze Tier)
    if event.available_tickets > 0:
        event.available_tickets -= 1
        event.save()
        
        reservation = Reservation.create(event=event, user_email=user_email)
        # Avoid circular serialization issues with max_depth
        return jsonify({
            "message": "Reservation successful",
            "reservation": model_to_dict(reservation, max_depth=1)
        }), 201
    else:
        return jsonify({"error": "Sold out"}), 400
