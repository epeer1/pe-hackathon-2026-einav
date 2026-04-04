from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.database import init_db
from app.error_log import record_error, get_errors
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)

    # ── Security: Request size limit (1MB max) ────────────────
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

    # ── Security: Rate Limiting ───────────────────────────────
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per minute"],
        storage_uri="memory://",
    )

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee
    from app.database import db
    db.create_tables([models.Event, models.Reservation, models.ErrorLog], safe=True)

    register_routes(app)

    # Exempt high-frequency endpoints from default rate limit
    from app.routes.telemetry import telemetry_bp
    from app.routes.reservations import reservations_bp
    limiter.exempt(telemetry_bp)
    limiter.exempt(reservations_bp)

    @app.route("/health")
    @limiter.exempt
    def health():
        return jsonify(status="ok")

    @app.route("/api/logs")
    @limiter.exempt
    def api_logs():
        return jsonify(get_errors())

    @app.route("/api/ping")
    @limiter.limit("5 per minute")
    def ping():
        return jsonify({"pong": True})

    # ── Security: Rate limit error returns JSON ───────────────
    @app.errorhandler(429)
    def rate_limit_error(e):
        return jsonify({"error": "Rate limit exceeded", "details": str(e.description)}), 429

    @app.errorhandler(413)
    def payload_too_large(e):
        return jsonify({"error": "Payload too large (max 1MB)"}), 413

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
        app.logger.exception("Unhandled exception: %s", e)
        record_error(500, str(e), request.method, request.path)
        return jsonify({"error": "Internal server error"}), 500

    @app.after_request
    def after_request_hook(response):
        from app.routes.telemetry import bump_request_counter
        bump_request_counter()

        # ── Security Headers ──────────────────────────────────
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Cache-Control'] = 'no-store'

        if response.status_code >= 400 and request.path != "/api/logs":
            error_msg = ""
            try:
                error_msg = response.get_json().get("error", "")
            except Exception:
                pass
            record_error(response.status_code, error_msg, request.method, request.path)
        return response

    return app
