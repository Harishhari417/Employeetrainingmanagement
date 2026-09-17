from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from db import db

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

@notifications_bp.get("")
@jwt_required()
def notifications():
    claims = get_jwt()
    role = claims.get("role")
    employee_id = claims.get("employeeId")
    department = claims.get("department")
    items = []

    if role == "EMPLOYEE":
        pending = db.training_participants.count_documents({"employeeId": employee_id, "feedbackStatus": "Pending"})
        if pending:
            items.append({"type": "feedback", "severity": "high", "title": "Feedback pending", "message": f"{pending} training feedback response(s) need your attention."})
        due = db.effectiveness_evaluations.count_documents({"employeeId": employee_id, "status": {"$in": ["Pending", "Overdue"]}})
        if due:
            items.append({"type": "evaluation", "severity": "medium", "title": "Evaluation due", "message": f"{due} effectiveness evaluation(s) are pending."})
    else:
        if role == "MANAGER":
            ids = [x.get("employeeId") for x in db.employees.find({"department": department}, {"employeeId": 1})]
            base = {"employeeId": {"$in": ids}}
        else:
            base = {}

        pending_feedback = db.training_participants.count_documents({**base, "feedbackStatus": "Pending"})
        if pending_feedback:
            items.append({"type": "feedback", "severity": "medium", "title": "Feedback responses pending", "message": f"{pending_feedback} participant feedback response(s) are still pending."})

        pending_eval = db.effectiveness_evaluations.count_documents({**base, "status": {"$in": ["Pending", "Overdue"]}})
        if pending_eval:
            items.append({"type": "evaluation", "severity": "high", "title": "Effectiveness reviews due", "message": f"{pending_eval} three-month evaluation(s) require attention."})

        upcoming_cutoff = datetime.now(timezone.utc) + timedelta(days=7)
        upcoming = db.trainings.count_documents({"status": "Scheduled", "trainingDate": {"$lte": upcoming_cutoff.isoformat()}})
        if upcoming:
            items.append({"type": "training", "severity": "low", "title": "Upcoming training", "message": f"{upcoming} scheduled training session(s) are within the next 7 days."})

    return jsonify({"count": len(items), "items": items})
