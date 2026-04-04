from flask import Blueprint, request, jsonify
from playhouse.shortcuts import model_to_dict
from peewee import IntegrityError
from app.models.flash_sale import Event, Reservation

reservations_bp = Blueprint("reservations", __name__)

@reservations_bp.route("/admin/event", methods=["POST"])
def create_event():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    name = data.get("name")
    total_tickets = data.get("total_tickets")

    # Validate required fields
    if not name or not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Missing or invalid 'name'"}), 400

    if total_tickets is None:
        return jsonify({"error": "Missing 'total_tickets'"}), 400

    # Validate data types and values
    if not isinstance(total_tickets, int) or isinstance(total_tickets, bool):
        return jsonify({"error": "'total_tickets' must be a positive integer"}), 400

    if total_tickets <= 0:
        return jsonify({"error": "'total_tickets' must be a positive integer"}), 400

    try:
        event = Event.create(
            name=name.strip(),
            total_tickets=total_tickets,
            available_tickets=total_tickets
        )
        return jsonify(model_to_dict(event)), 201
    except IntegrityError:
        return jsonify({"error": "Event already exists"}), 400


@reservations_bp.route("/reserve", methods=["POST"])
def reserve():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    event_id = data.get("event_id")
    user_email = data.get("user_email")

    # Validate required fields
    if event_id is None:
        return jsonify({"error": "Missing event_id"}), 400

    if not user_email or not isinstance(user_email, str) or not user_email.strip():
        return jsonify({"error": "Missing or invalid user_email"}), 400

    # Basic email format check
    user_email = user_email.strip()
    if "@" not in user_email:
        return jsonify({"error": "Invalid email format"}), 400

    from app.database import db

    try:
        with db.atomic():
            event = Event.select().where(Event.id == event_id).for_update().get()

            # Check if event is still active
            if not event.active:
                return jsonify({"error": "Event is no longer active"}), 400

            if event.available_tickets > 0:
                event.available_tickets -= 1
                event.save()

                try:
                    with db.atomic():  # Nested savepoint
                        reservation = Reservation.create(event=event, user_email=user_email)
                except IntegrityError:
                    # Duplicate reservation — rollback the ticket decrement
                    event.available_tickets += 1
                    event.save()
                    return jsonify({"error": "User already has a reservation for this event"}), 409

                return jsonify({
                    "message": "Reservation successful",
                    "reservation": model_to_dict(reservation, max_depth=1)
                }), 201
            else:
                return jsonify({"error": "Sold out"}), 400

    except Event.DoesNotExist:
        return jsonify({"error": "Event not found"}), 404


@reservations_bp.route("/admin/event/<int:event_id>/deactivate", methods=["POST"])
def deactivate_event(event_id):
    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        return jsonify({"error": "Event not found"}), 404

    event.active = False
    event.save()
    return jsonify({"message": "Event deactivated", "event": model_to_dict(event)}), 200

