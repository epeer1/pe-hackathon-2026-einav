from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from app.database import init_db
from app.error_log import record_error, get_errors
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee
    from app.database import db
    db.create_tables([models.Event, models.Reservation, models.ErrorLog], safe=True)

    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    # Production Engineering: Strict JSON Error Handlers
    @app.errorhandler(404)
    def not_found_error(e):
        record_error(404, "Resource not found", request.method, request.path)
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        record_error(405, "Method not allowed", request.method, request.path)
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        record_error(500, "Internal server error", request.method, request.path)
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        record_error(500, str(e), request.method, request.path)
        return jsonify({"error": "Unexpected failure", "details": str(e)}), 500

    @app.route("/api/logs")
    def api_logs():
        return jsonify(get_errors())

    @app.after_request
    def after_request_hook(response):
        from app.routes.telemetry import bump_request_counter
        bump_request_counter()
        if response.status_code >= 400 and request.path != "/api/logs":
            error_msg = ""
            try:
                error_msg = response.get_json().get("error", "")
            except Exception:
                pass
            record_error(response.status_code, error_msg, request.method, request.path)
        return response

    return app
