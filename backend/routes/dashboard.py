from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from db import db

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

def count_for_role(role, department=None, employee_id=None):
    if role == "EMPLOYEE":
        pquery = {"employeeId": employee_id}
        feedback = db.feedback.count_documents({"employeeId": employee_id})
        participants = list(db.training_participants.find(pquery, {"attendance": 1}))
        return participants, feedback
    if role == "MANAGER":
        ids = [x.get("employeeId") for x in db.employees.find({"department": department}, {"employeeId": 1})]
        participants = list(db.training_participants.find({"employeeId": {"$in": ids}}, {"attendance": 1}))
        feedback = db.feedback.count_documents({"employeeId": {"$in": ids}})
        return participants, feedback
    participants = list(db.training_participants.find({}, {"attendance": 1}))
    return participants, db.feedback.count_documents({})

@bp.get("/admin")
@jwt_required()
def admin_dashboard():
    claims = get_jwt(); role = claims.get("role")
    participants, feedback_count = count_for_role(role, claims.get("department"), claims.get("employeeId"))
    if role == "EMPLOYEE":
        training_count = db.training_participants.count_documents({"employeeId": claims.get("employeeId")})
        completed = db.training_participants.count_documents({"employeeId": claims.get("employeeId"), "completionStatus": "Completed"})
        employees = 1
    elif role == "MANAGER":
        ids = [x.get("employeeId") for x in db.employees.find({"department": claims.get("department")}, {"employeeId": 1})]
        training_count = len({x.get("trainingId") for x in db.training_participants.find({"employeeId": {"$in": ids}}, {"trainingId": 1})})
        completed = db.training_participants.count_documents({"employeeId": {"$in": ids}, "completionStatus": "Completed"})
        employees = len(ids)
    else:
        training_count = db.trainings.count_documents({}); completed = db.trainings.count_documents({"status":"Completed"}); employees = db.employees.count_documents({"status":"Active"})
    present = sum(1 for p in participants if p.get("attendance") == "Present")
    return jsonify({
        "totalTrainings": training_count, "completedTrainings": completed, "totalEmployees": employees,
        "attendancePercentage": round(present / len(participants) * 100, 1) if participants else 0,
        "feedbackCount": feedback_count,
        "pendingFeedback": db.training_participants.count_documents({"feedbackStatus":"Pending", **({"employeeId": claims.get("employeeId")} if role == "EMPLOYEE" else {})}),
        "pendingEvaluations": db.effectiveness_evaluations.count_documents({"status":{"$in":["Pending","Overdue"]}, **({"employeeId": claims.get("employeeId")} if role == "EMPLOYEE" else {})}),
    })
