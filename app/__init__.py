from pathlib import Path
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "public.login"
login_manager.login_message = "Для доступа к разделу необходимо войти в систему."
login_manager.login_message_category = "warning"


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["GENERATED_DOCS_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["GENERATED_REPORTS_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.public import public_bp
    from app.routes.client import client_bp
    from app.routes.specialist import specialist_bp
    from app.routes.admin import admin_bp
    from app.routes.downloads import downloads_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(specialist_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(downloads_bp)

    return app
