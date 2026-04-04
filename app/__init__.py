from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from app.database import init_db
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee
    from app.database import db
    db.create_tables([models.Event, models.Reservation], safe=True)

    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    # Production Engineering: Strict JSON Error Handlers
    @app.errorhandler(404)
    def not_found_error(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        # Catches uncaught database failures or code bugs seamlessly
        return jsonify({"error": "Unexpected failure", "details": str(e)}), 500

    return app
