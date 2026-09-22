from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
from db import db

evaluations_bp = Blueprint("evaluations", __name__, url_prefix="/api/evaluations")


def serialize(doc):
    if not doc:
        return None
    d = dict(doc)
    d["_id"] = str(d["_id"])
    for key in ("dueDate", "completedAt"):
        if d.get(key):
            d[key] = d[key].isoformat() if hasattr(d[key], "isoformat") else d[key]
    return d


def sync_due_evaluations():
    for training in db.trainings.find({"status": "Completed"}):
        completed = training.get("completedAt") or training.get("trainingDate")
        if not completed:
            continue
        try:
            base = datetime.fromisoformat(completed.replace("Z", "+00:00")) if isinstance(completed, str) else completed
            if base.tzinfo is None:
                base = base.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        due = base + timedelta(days=90)
        participants = db.training_participants.find({"trainingId": str(training["_id"])}, {"employeeId": 1})
        for participant in participants:
            employee_id = participant.get("employeeId")
            if not employee_id:
                continue
            db.effectiveness_evaluations.update_one(
                {"trainingId": str(training["_id"]), "employeeId": employee_id},
                {"$setOnInsert": {"trainingId": str(training["_id"]), "employeeId": employee_id, "dueDate": due, "status": "Pending", "createdAt": datetime.now(timezone.utc)}},
                upsert=True,
            )


@evaluations_bp.get("")
@jwt_required()
def list_evaluations():
    sync_due_evaluations()
    claims = get_jwt()
    query = {}
    if claims.get("role") == "EMPLOYEE":
        query["employeeId"] = claims.get("employeeId")
    elif claims.get("role") == "MANAGER":
        ids = [x.get("employeeId") for x in db.employees.find({"department": claims.get("department")}, {"employeeId": 1, "_id": 0}) if x.get("employeeId")]
        query["employeeId"] = {"$in": ids}
    rows = [serialize(x) for x in db.effectiveness_evaluations.find(query).sort("dueDate", 1)]
    for row in rows:
        emp = db.employees.find_one({"employeeId": row.get("employeeId")}, {"_id": 0, "name": 1, "department": 1, "email": 1}) or {}
        try:
            training = db.trainings.find_one({"_id": ObjectId(row["trainingId"])}, {"title": 1, "trainingDate": 1}) or {}
        except Exception:
            training = {}
        row["employeeName"] = emp.get("name", row.get("employeeId"))
        row["department"] = emp.get("department", "")
        row["employeeEmail"] = emp.get("email", "")
        row["trainingTitle"] = training.get("title", "")
    return jsonify(rows)


@evaluations_bp.put("/<evaluation_id>")
@jwt_required()
def update_evaluation(evaluation_id):
    claims = get_jwt()
    if claims.get("role") not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "Manager or HR Admin permission required"}), 403
    try:
        object_id = ObjectId(evaluation_id)
    except Exception:
        return jsonify({"message": "Invalid evaluation id"}), 400
    existing = db.effectiveness_evaluations.find_one({"_id": object_id})
    if not existing:
        return jsonify({"message": "Evaluation not found"}), 404
    if claims.get("role") == "MANAGER":
        employee = db.employees.find_one({"employeeId": existing.get("employeeId")}, {"department": 1})
        if not employee or employee.get("department") != claims.get("department"):
            return jsonify({"message": "Managers can only update evaluations for their department"}), 403
    payload = request.get_json(silent=True) or {}
    fields = {}
    for field in ["requiredLevel", "earlierLevel", "presentLevel", "suggestions", "status"]:
        if field in payload:
            fields[field] = payload[field]
    for field in ["requiredLevel", "earlierLevel", "presentLevel"]:
        if field in fields:
            try:
                fields[field] = int(fields[field])
                if fields[field] < 1 or fields[field] > 5:
                    raise ValueError
            except Exception:
                return jsonify({"message": f"{field} must be between 1 and 5"}), 400
    if fields.get("status") == "Completed":
        fields["completedAt"] = datetime.now(timezone.utc)
    if not fields:
        return jsonify({"message": "No fields to update"}), 400
    db.effectiveness_evaluations.update_one({"_id": object_id}, {"$set": fields})
    return jsonify({"message": "Evaluation updated"})
