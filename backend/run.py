from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import FRONTEND_ORIGIN, JWT_SECRET_KEY

from routes.auth import auth_bp
from routes.dashboard import bp as dashboard_bp
from routes.notifications import bp as notifications_bp
from routes.analytics import bp as analytics_bp
from routes.evaluations import bp as evaluations_bp
from routes.reports import bp as reports_bp

from routes.attendance import attendance_bp
from routes.departments import departments_bp
from routes.employees import employees_bp
from routes.feedback import feedback_bp
from routes.trainings import trainings_bp
from routes.health import health_bp


app = Flask(__name__)


# =========================================================
# JWT CONFIGURATION
# =========================================================

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

jwt = JWTManager(app)


# =========================================================
# CORS CONFIGURATION
# =========================================================

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [FRONTEND_ORIGIN]
        }
    },
    supports_credentials=True,
)


# =========================================================
# API BLUEPRINTS
# =========================================================

app.register_blueprint(auth_bp)

app.register_blueprint(dashboard_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(evaluations_bp)
app.register_blueprint(reports_bp)

app.register_blueprint(attendance_bp)
app.register_blueprint(departments_bp)
app.register_blueprint(employees_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(trainings_bp)

app.register_blueprint(health_bp)


# =========================================================
# APPLICATION START
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )