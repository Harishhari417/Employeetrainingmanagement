from datetime import datetime, timezone
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
    if ids is not None:
        query["employeeId"] = {"$in": ids}
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
    required = ["trainingId", "employeeId", "ratings"]
    missing = [field for field in required if payload.get(field) in (None, "", {})]
    if missing:
        return jsonify({"message": "Missing required fields", "fields": missing}), 400
    return save_feedback(payload, claims)


@feedback_bp.put("")
@jwt_required()
def edit_feedback():
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}
    required = ["trainingId", "employeeId", "ratings"]
    missing = [field for field in required if payload.get(field) in (None, "", {})]
    if missing:
        return jsonify({"message": "Missing required fields", "fields": missing}), 400
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


@feedback_bp.get("/management")
@jwt_required()
def management_feedback_list():
    claims = get_jwt()
    role = claims.get("role")
    if role not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "HR Admin or Manager permission required"}), 403

    query = {}
    if role == "MANAGER":
        query["departments"] = claims.get("department")
    trainings = list(db.trainings.find(query).sort("startDate", -1).limit(500))
    reviewer_id = claims.get("employeeId")
    records = {
        row.get("trainingId"): row
        for row in db.management_feedback.find({"reviewerId": reviewer_id})
    }
    result = []
    for training in trainings:
        tid = str(training["_id"])
        record = records.get(tid, {})
        result.append({
            "_id": tid,
            "title": training.get("title", ""),
            "trainingType": training.get("trainingType", ""),
            "trainerName": training.get("trainerName", ""),
            "startDate": training.get("startDate", training.get("trainingDate")),
            "endDate": training.get("endDate"),
            "status": training.get("status", "Upcoming"),
            "departments": training.get("departments", []),
            "feedbackStatus": record.get("status", "Pending"),
            "rating": record.get("rating", ""),
            "remarks": record.get("remarks", ""),
            "submittedAt": record.get("submittedAt"),
        })
    return jsonify(result)


@feedback_bp.post("/management")
@jwt_required()
def save_management_feedback():
    claims = get_jwt()
    role = claims.get("role")
    if role not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "HR Admin or Manager permission required"}), 403

    payload = request.get_json(silent=True) or {}
    training_id = str(payload.get("trainingId", "")).strip()
    rating = payload.get("rating")
    remarks = str(payload.get("remarks", "")).strip()
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        rating = 0

    if not training_id or rating < 1 or rating > 5:
        return jsonify({"message": "Training and a rating from 1 to 5 are required"}), 400

    from bson import ObjectId
    if not ObjectId.is_valid(training_id):
        return jsonify({"message": "Invalid training"}), 400
    training = db.trainings.find_one({"_id": ObjectId(training_id)})
    if not training:
        return jsonify({"message": "Training not found"}), 404

    if role == "MANAGER" and claims.get("department") not in training.get("departments", []):
        ids = [x.get("employeeId") for x in db.employees.find({"department": claims.get("department")}, {"employeeId": 1, "_id": 0})]
        if not db.training_participants.count_documents({"trainingId": training_id, "employeeId": {"$in": ids}}):
            return jsonify({"message": "This training is not assigned to your department"}), 403

    now = datetime.now(timezone.utc)
    db.management_feedback.update_one(
        {"trainingId": training_id, "reviewerId": claims.get("employeeId")},
        {"$set": {
            "trainingId": training_id,
            "reviewerId": claims.get("employeeId"),
            "reviewerRole": role,
            "rating": rating,
            "remarks": remarks,
            "status": "Submitted",
            "submittedAt": now,
            "updatedAt": now,
        }},
        upsert=True,
    )
    return jsonify({"message": "Overall training feedback submitted successfully"}), 200
