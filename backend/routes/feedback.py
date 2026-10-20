from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from db import db

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


def visible_employee_ids(claims):
    role = claims.get("role")
    if role == "EMPLOYEE":
        return [claims.get("employeeId")]
    if role == "MANAGER":
        return [x.get("employeeId") for x in db.employees.find({"department": claims.get("department")}, {"employeeId": 1, "_id": 0}) if x.get("employeeId")]
    return None


@feedback_bp.get("")
@jwt_required()
def list_feedback():
    claims = get_jwt()
    query = {}
    if request.args.get("trainingId"):
        query["trainingId"] = request.args["trainingId"]
    ids = visible_employee_ids(claims)
    # A trainer sees responses for their own trainings; trainees still see their own.
    if claims.get("role") in {"EMPLOYEE", "MANAGER"}:
        trainer_training_ids = [str(x["_id"]) for x in db.trainings.find({"trainerEmployeeId": claims.get("employeeId")}, {"_id": 1})]
        own_employee_ids = ids or [claims.get("employeeId")]
        query["$or"] = [{"employeeId": {"$in": own_employee_ids}}, {"trainerEmployeeId": claims.get("employeeId")}, {"trainingId": {"$in": trainer_training_ids}}]
    records = list(db.feedback.find(query, {"_id": 0}).sort("submittedAt", -1).limit(1000))
    for row in records:
        employee = db.employees.find_one({"employeeId": row.get("employeeId")}, {"name": 1, "department": 1, "_id": 0}) or {}
        row["employeeName"] = employee.get("name", row.get("employeeId", ""))
        row["department"] = employee.get("department", "")
        try:
            from bson import ObjectId
            training = db.trainings.find_one({"_id": ObjectId(row.get("trainingId"))}, {"title": 1, "_id": 0}) or {}
        except Exception:
            training = {}
        row["trainingTitle"] = training.get("title", "")
        row["trainerEmployeeId"] = ""
        row["trainerName"] = ""
        try:
            training_doc = db.trainings.find_one({"_id": ObjectId(row.get("trainingId"))}, {"trainerEmployeeId": 1, "trainerName": 1}) or {}
            row["trainerEmployeeId"] = training_doc.get("trainerEmployeeId", "")
            row["trainerName"] = training_doc.get("trainerName", "")
        except Exception:
            pass
    return jsonify(records)


def save_feedback(payload, claims, existing=None):
    employee_id = str(payload.get("employeeId", "")).strip()
    if claims.get("role") == "EMPLOYEE" and employee_id != claims.get("employeeId"):
        return jsonify({"message": "You can only submit your own feedback"}), 403
    if claims.get("role") == "MANAGER":
        employee = db.employees.find_one({"employeeId": employee_id})
        if not employee or employee.get("department") != claims.get("department"):
            return jsonify({"message": "Managers can only access feedback for their department"}), 403
    participant = db.training_participants.find_one({"trainingId": payload.get("trainingId"), "employeeId": employee_id})
    if not participant:
        return jsonify({"message": "Employee is not assigned to this training"}), 400
    if participant.get("attendance") == "Absent":
        return jsonify({"message": "Absent participants cannot submit feedback"}), 400
    data = dict(payload)
    data["employeeId"] = employee_id
    training = db.trainings.find_one({"_id": ObjectId(payload.get("trainingId"))}) if ObjectId.is_valid(str(payload.get("trainingId", ""))) else None
    if training:
        data["trainerEmployeeId"] = training.get("trainerEmployeeId", "")
        data["trainerName"] = training.get("trainerName", "")
    data["status"] = "Submitted"
    data["submittedAt"] = datetime.now(timezone.utc)
    db.feedback.update_one({"trainingId": data["trainingId"], "employeeId": employee_id}, {"$set": data}, upsert=True)
    db.training_participants.update_one({"trainingId": data["trainingId"], "employeeId": employee_id}, {"$set": {"feedbackStatus": "Submitted"}})
    return jsonify({"message": "Feedback submitted"}), 200


@feedback_bp.post("")
@jwt_required()
def create_feedback():
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}
    required = ["trainingId", "employeeId", "ratings", "knowledgeBefore", "knowledgeAfter", "bestModule", "missedModule", "majorLearning", "ideasToImplement", "remarks"]
    missing = [field for field in required if payload.get(field) in (None, "", {})]
    rating_keys = ["Programme Design", "Presentation of Information", "Amount of Information", "Administrative arrangements", "overall"]
    missing_ratings = [key for key in rating_keys if not (payload.get("ratings") or {}).get(key)]
    if missing or missing_ratings:
        return jsonify({"message": "Complete every required feedback field", "fields": missing + missing_ratings}), 400
    return save_feedback(payload, claims)


@feedback_bp.put("")
@jwt_required()
def edit_feedback():
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}
    required = ["trainingId", "employeeId", "ratings", "knowledgeBefore", "knowledgeAfter", "bestModule", "missedModule", "majorLearning", "ideasToImplement", "remarks"]
    missing = [field for field in required if payload.get(field) in (None, "", {})]
    rating_keys = ["Programme Design", "Presentation of Information", "Amount of Information", "Administrative arrangements", "overall"]
    missing_ratings = [key for key in rating_keys if not (payload.get("ratings") or {}).get(key)]
    if missing or missing_ratings:
        return jsonify({"message": "Complete every required feedback field", "fields": missing + missing_ratings}), 400
    existing = db.feedback.find_one({"trainingId": payload.get("trainingId"), "employeeId": payload.get("employeeId")})
    if not existing:
        return jsonify({"message": "Feedback not found"}), 404
    return save_feedback(payload, claims, existing)


@feedback_bp.post("/reopen")
@jwt_required()
def reopen_feedback():
    if get_jwt().get("role") not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "Manager or HR Admin permission required"}), 403
    payload = request.get_json(silent=True) or {}
    if get_jwt().get("role") == "MANAGER":
        employee = db.employees.find_one({"employeeId": payload.get("employeeId")})
        if not employee or employee.get("department") != get_jwt().get("department"):
            return jsonify({"message": "Managers can only reopen feedback for their department"}), 403
    result = db.feedback.update_one({"trainingId": payload.get("trainingId"), "employeeId": payload.get("employeeId")}, {"$set": {"status": "Draft"}, "$unset": {"submittedAt": ""}})
    db.training_participants.update_one({"trainingId": payload.get("trainingId"), "employeeId": payload.get("employeeId")}, {"$set": {"feedbackStatus": "Pending"}})
    return jsonify({"message": "Feedback reopened", "updated": result.modified_count > 0})
