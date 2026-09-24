from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from app.routes import main_bp
    from app.routes.auth import auth_bp
    from app.routes.trader import trader_bp
    from app.routes.owner import owner_bp
    from app.routes.admin import admin_bp
    from app.routes.trucks import trucks_bp
    from app.routes.requests import requests_bp
    from app.routes.bookings import bookings_bp
    from app.routes.notifications import notifications_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(trader_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(trucks_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(profile_bp)

    with app.app_context():
        db.create_all()

    return app