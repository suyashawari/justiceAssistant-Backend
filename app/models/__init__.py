# # app/__init__.py

# import os
# from dotenv import load_dotenv
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_cors import CORS
# from flask_jwt_extended import JWTManager
# from flask_migrate import Migrate

# load_dotenv()

# db = SQLAlchemy()
# jwt = JWTManager()
# migrate = Migrate()

# # The celery_init_app function has been completely removed.

# def create_app():
#     app = Flask(__name__, instance_relative_config=False)

#     # --- Core Configurations ---
#     app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
#     app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#     app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-key")
    
#     # The app.config["CELERY"] dictionary has been removed.

#     # --- Initialize Extensions ---
#     db.init_app(app)
#     jwt.init_app(app)
#     migrate.init_app(app, db)
    
#     # The celery_init_app() call has been removed.

#     # --- CORS and Blueprints ---
#     # CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
#     CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
#     from app.api.main_routes import main as main_blueprint
#     from app.api.auth_routes import auth as auth_blueprint
#     from app.api.ai_routes import ai as ai_blueprint
#     from app.api.report_routes import report as report_blueprint
#     from app.api.dashboard_route import dashboard
#     from app.api.admin_routes import admin_bp

#     app.register_blueprint(main_blueprint)
#     app.register_blueprint(auth_blueprint, url_prefix="/auth")
#     app.register_blueprint(report_blueprint, url_prefix="/report")
#     app.register_blueprint(ai_blueprint, url_prefix="/ai")
#     app.register_blueprint(dashboard)
#     app.register_blueprint(admin_bp, url_prefix="/api")

#     return app





import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
load_dotenv()
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
def create_app():
    app = Flask(__name__, instance_relative_config=False)

    # --- ADDED: Centralized CORS Configuration for the entire app ---
    # This single line handles CORS for all routes and blueprints.
    CORS(app, supports_credentials=True)
    # -----------------------------------------------------------------

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-key")
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    from app.api.main_routes import main as main_blueprint
    from app.api.auth_routes import auth as auth_blueprint
    from app.api.ai_routes import ai as ai_blueprint
    from app.api.report_routes import report as report_blueprint
    from app.api.dashboard_route import dashboard
    from app.api.admin_routes import admin_bp

    # --- REMOVED: All redundant, blueprint-specific CORS lines ---
    # CORS(auth_blueprint, supports_credentials=True, origins="*")
    # CORS(ai_blueprint, supports_credentials=True, origins="*")
    # CORS(dashboard, supports_credentials=True, origins="*")
    # CORS(main_blueprint, supports_credentials=True, origins="*")
    # CORS(report_blueprint, supports_credentials=True, origins="*")
    # CORS(admin_bp, supports_credentials=True, origins="*")
    # -------------------------------------------------------------

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(report_blueprint, url_prefix="/report")
    app.register_blueprint(ai_blueprint, url_prefix="/ai")
    app.register_blueprint(dashboard)
    app.register_blueprint(admin_bp, url_prefix="/api")
    return app