def register_routes(app):
    """Register all route blueprints with the Flask app.

    Add your blueprints here. Example:
        from app.routes.products import products_bp
        app.register_blueprint(products_bp)
    """
    from app.routes.reservations import reservations_bp
    from app.routes.telemetry import telemetry_bp
    
    app.register_blueprint(reservations_bp)
    app.register_blueprint(telemetry_bp)
