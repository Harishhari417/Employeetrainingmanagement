from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from db import db


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def parse_filter_date(value, end=False):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            from zoneinfo import ZoneInfo
            dt = dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        return dt
    except Exception:
        return None


def date_query(start_date, end_date):
    query = {}
    start = parse_filter_date(start_date)
    end = parse_filter_date(end_date, True)
    if start:
        query["$gte"] = start.isoformat()
    if end:
        if len(end_date or "") == 10:
            end = end.replace(hour=23, minute=59, second=59)
        query["$lte"] = end.isoformat()
    return {"trainingDate": query} if query else {}


@dashboard_bp.get("")
@jwt_required()
def dashboard():
    try:
        claims = get_jwt()
        role = claims.get("role")
        employee_id = claims.get("employeeId")
        department = claims.get("department")

        if role not in {"HR_ADMIN", "MANAGER", "EMPLOYEE"}:
            return jsonify({"message": "Invalid user role"}), 403

        start_date = request.args.get("startDate", "").strip()
        end_date = request.args.get("endDate", "").strip()
        training_query = date_query(start_date, end_date)

        if role == "EMPLOYEE":
            employee_ids = [employee_id]
        elif role == "MANAGER":
            employee_ids = [
                x.get("employeeId")
                for x in db.employees.find(
                    {"department": department}, {"employeeId": 1, "_id": 0}
                )
                if x.get("employeeId")
            ]
        else:
            employee_ids = None

        participant_filter = {}
        if employee_ids is not None:
            participant_filter["employeeId"] = {"$in": employee_ids}

        training_ids = db.training_participants.distinct("trainingId", participant_filter) if participant_filter else db.training_participants.distinct("trainingId")
        if role == "EMPLOYEE" and employee_id:
            training_filter = {"_id": {"$in": []}}
            try:
                from bson import ObjectId
                training_filter["_id"] = {"$in": [ObjectId(x) for x in training_ids if ObjectId.is_valid(x)]}
            except Exception:
                pass
        elif role == "MANAGER":
            from bson import ObjectId
            ids = [ObjectId(x) for x in training_ids if ObjectId.is_valid(x)]
            training_filter = {"_id": {"$in": ids}}
        else:
            training_filter = {}

        training_filter.update(training_query)
        total_trainings = db.trainings.count_documents(training_filter)
        completed_trainings = db.trainings.count_documents({**training_filter, "status": "Completed"})

        participant_query = dict(participant_filter)
        if training_ids:
            participant_query["trainingId"] = {"$in": [str(x) for x in training_ids]}
        elif role != "HR_ADMIN":
            participant_query["trainingId"] = {"$in": []}

        participants = list(db.training_participants.find(participant_query, {"attendance": 1, "feedbackStatus": 1, "completionStatus": 1, "employeeId": 1, "trainingId": 1}))
        attendance_total = len(participants)
        attendance_present = sum(1 for p in participants if str(p.get("attendance", "")).lower() == "present")
        attendance_percentage = round(attendance_present / attendance_total * 100, 1) if attendance_total else 0
        feedback_count = db.feedback.count_documents({**participant_filter, "status": "Submitted"}) if participant_filter else db.feedback.count_documents({"status": "Submitted"})
        pending_feedback = sum(1 for p in participants if str(p.get("feedbackStatus", "Pending")).lower() in {"pending", "due", "not submitted"})

        evaluation_query = dict(participant_filter)
        pending_evaluations = db.effectiveness_evaluations.count_documents({**evaluation_query, "status": {"$in": ["Pending", "Overdue", "Due"]}})
        evaluation_feedback = db.effectiveness_evaluations.count_documents({**evaluation_query, "suggestions": {"$exists": True, "$nin": [None, ""]}})

        type_stats = []
        for training_type in ["Technical", "Behavioural", "Leadership"]:
            type_query = {**training_filter, "trainingType": training_type}
            type_stats.append({"type": training_type, "count": db.trainings.count_documents(type_query)})

        return jsonify({
            "totalTrainings": total_trainings,
            "completedTrainings": completed_trainings,
            "totalEmployees": db.employees.count_documents({"department": department}) if role == "MANAGER" else (db.employees.count_documents({"employeeId": employee_id}) if role == "EMPLOYEE" else db.employees.count_documents({"status": {"$ne": "Inactive"}})),
            "attendancePercentage": attendance_percentage,
            "feedbackCount": feedback_count,
            "pendingFeedback": pending_feedback,
            "pendingEvaluations": pending_evaluations,
            "evaluationFeedback": evaluation_feedback,
            "trainingTypes": type_stats,
        }), 200
    except Exception as error:
        print("DASHBOARD ERROR:", error)
        return jsonify({"message": "Failed to load dashboard", "error": str(error)}), 500
