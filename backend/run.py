from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config

from routes.auth import auth_bp
from routes.feedback import feedback_bp
from routes.attendance import attendance_bp
from routes.trainings import trainings_bp
from routes.employees import employees_bp
from routes.departments import departments_bp
from routes.dashboard import dashboard_bp
from routes.evaluations import evaluations_bp
from routes.analytics import analytics_bp
from routes.notifications import notifications_bp
from routes.reports import reports_bp


app = Flask(__name__)

# Load configuration
app.config.from_object(Config)


# --------------------------------
# CORS
# --------------------------------

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                Config.FRONTEND_ORIGIN,
                "http://localhost:5173",
            ],
            "methods": [
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS",
            ],
            "allow_headers": [
                "Content-Type",
                "Authorization",
            ],
            "supports_credentials": True,
        }
    },
)


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return "", 200


# --------------------------------
# JWT
# --------------------------------

JWTManager(app)


# --------------------------------
# Register Blueprints
# --------------------------------

app.register_blueprint(auth_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(trainings_bp)
app.register_blueprint(employees_bp)
app.register_blueprint(departments_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(evaluations_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(reports_bp)


# --------------------------------
# Health Check
# --------------------------------

@app.route("/health")
def health():
    return {
        "status": "ok"
    }, 200


# --------------------------------
# Local Development
# --------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )