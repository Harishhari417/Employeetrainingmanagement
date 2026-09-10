from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import JWT_SECRET_KEY, FRONTEND_ORIGIN
from routes.health import health_bp
from routes.feedback import feedback_bp
from routes.attendance import attendance_bp
from routes.trainings import trainings_bp
from routes.employees import employees_bp
from routes.departments import departments_bp
from routes.dashboard import bp as dashboard_bp
from routes.evaluations import bp as evaluations_bp
from routes.analytics import bp as analytics_bp
from routes.auth import auth_bp, ensure_admin_user
from db import create_indexes
from routes.notifications import bp as notifications_bp
from routes.reports import bp as reports_bp

def create_app():
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def home():
        return {
            "message": "Employee Training Management API is running",
            "status": "success"
        }, 200

    app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

    from config import JWT_ACCESS_TOKEN_EXPIRES
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = JWT_ACCESS_TOKEN_EXPIRES

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": FRONTEND_ORIGIN
            }
        }
    )

    JWTManager(app)

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(feedback_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(trainings_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(evaluations_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(reports_bp)

    create_indexes()
    ensure_admin_user()

    return app
    

   
