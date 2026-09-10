from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from db import db

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")

@feedback_bp.get("")
@jwt_required()
def list_feedback():
    claims = get_jwt()
    query = {}
    if request.args.get("trainingId"):
        query["trainingId"] = request.args["trainingId"]
    if claims.get("role") == "EMPLOYEE":
        query["employeeId"] = claims.get("employeeId")
    records = list(db.feedback.find(query, {"_id": 0}).sort("submittedAt", -1).limit(500))
    return jsonify(records)

@feedback_bp.post("")
@jwt_required()
def create_feedback():
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}
    required = ["trainingId", "employeeId", "ratings"]
    missing = [field for field in required if payload.get(field) in (None, "", {})]
    if missing:
        return jsonify({"message": "Missing required fields", "fields": missing}), 400
    if claims.get("role") == "EMPLOYEE" and payload["employeeId"] != claims.get("employeeId"):
        return jsonify({"message": "You can only submit your own feedback"}), 403
    participant = db.training_participants.find_one({"trainingId": payload["trainingId"], "employeeId": payload["employeeId"]})
    if participant and participant.get("attendance") == "Absent":
        return jsonify({"message": "Absent participants cannot submit feedback"}), 400
    existing = db.feedback.find_one({"trainingId": payload["trainingId"], "employeeId": payload["employeeId"]})
    if existing and existing.get("submittedAt"):
        return jsonify({"message": "Feedback has already been submitted"}), 409
    payload["submittedAt"] = datetime.now(timezone.utc)
    payload["status"] = "Submitted"
    db.feedback.update_one(
        {"trainingId": payload["trainingId"], "employeeId": payload["employeeId"]},
        {"$set": payload},
        upsert=True,
    )
    db.training_participants.update_one(
        {"trainingId": payload["trainingId"], "employeeId": payload["employeeId"]},
        {"$set": {"feedbackStatus": "Submitted"}}, upsert=True,
    )
    return jsonify({"message": "Feedback submitted"}), 201

@feedback_bp.post("/reopen")
@jwt_required()
def reopen_feedback():
    if get_jwt().get("role") != "HR_ADMIN":
        return jsonify({"message": "HR Admin permission required"}), 403
    payload = request.get_json(silent=True) or {}
    result = db.feedback.update_one(
        {"trainingId": payload.get("trainingId"), "employeeId": payload.get("employeeId")},
        {"$unset": {"submittedAt": ""}, "$set": {"status": "Draft"}},
    )
    db.training_participants.update_one(
        {"trainingId": payload.get("trainingId"), "employeeId": payload.get("employeeId")},
        {"$set": {"feedbackStatus": "Pending"}},
    )
    return jsonify({"message": "Feedback reopened", "updated": result.modified_count > 0})
