from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from db import db
from bson import ObjectId

bp = Blueprint("evaluations", __name__, url_prefix="/api/evaluations")

def serialize(doc):
    if not doc: return None
    d = dict(doc); d["_id"] = str(d["_id"])
    for key in ("dueDate", "completedAt"):
        if d.get(key): d[key] = d[key].isoformat()
    return d

def sync_due_evaluations():
    trainings = list(db.trainings.find({"status": "Completed"}))
    for training in trainings:
        completed = training.get("completedAt") or training.get("trainingDate")
        if not completed: continue
        try:
            base = datetime.fromisoformat(completed.replace("Z", "+00:00")) if isinstance(completed, str) else completed
        except Exception:
            continue
        due = base + timedelta(days=90)
        participants = list(db.training_participants.find({"trainingId": str(training["_id"])}, {"employeeId": 1}))
        for p in participants:
            db.effectiveness_evaluations.update_one(
                {"trainingId": str(training["_id"]), "employeeId": p.get("employeeId")},
                {"$setOnInsert": {"trainingId": str(training["_id"]), "employeeId": p.get("employeeId"), "dueDate": due, "status": "Pending"}},
                upsert=True,
            )

@bp.get("")
@jwt_required()
def list_evaluations():
    sync_due_evaluations()
    claims = get_jwt(); query = {}
    if claims.get("role") == "EMPLOYEE": query["employeeId"] = claims.get("employeeId")
    if claims.get("role") == "MANAGER":
        ids = [e.get("employeeId") for e in db.employees.find({"department": claims.get("department")}, {"employeeId": 1})]
        query["employeeId"] = {"$in": ids}
    rows = [serialize(x) for x in db.effectiveness_evaluations.find(query).sort("dueDate", 1)]
    for row in rows:
        emp = db.employees.find_one({"employeeId": row.get("employeeId")}, {"_id": 0, "name": 1, "department": 1}) or {}
        try: training = db.trainings.find_one({"_id": ObjectId(row["trainingId"])}, {"title": 1}) or {}
        except Exception: training = {}
        row["employeeName"] = emp.get("name", row.get("employeeId")); row["department"] = emp.get("department", ""); row["trainingTitle"] = training.get("title", "")
    return jsonify(rows)

@bp.put("/<evaluation_id>")
@jwt_required()
def update_evaluation(evaluation_id):
    if get_jwt().get("role") not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "Manager or HR Admin permission required"}), 403
    from bson import ObjectId
    payload = request.get_json(silent=True) or {}
    fields = {k: payload[k] for k in ["requiredLevel", "earlierLevel", "presentLevel", "suggestions", "status"] if k in payload}
    if payload.get("status") == "Completed": fields["completedAt"] = datetime.now(timezone.utc)
    try:
        existing = db.effectiveness_evaluations.find_one({"_id": ObjectId(evaluation_id)})
    except Exception:
        return jsonify({"message": "Invalid evaluation id"}), 400
    if not existing:
        return jsonify({"message": "Evaluation not found"}), 404
    claims = get_jwt()
    if claims.get("role") == "MANAGER":
        employee = db.employees.find_one({"employeeId": existing.get("employeeId")}, {"department": 1})
        if not employee or employee.get("department") != claims.get("department"):
            return jsonify({"message": "Managers can only update evaluations for their department"}), 403
    if not fields:
        return jsonify({"message": "No fields to update"}), 400
    result = db.effectiveness_evaluations.update_one({"_id": ObjectId(evaluation_id)}, {"$set": fields})
    return jsonify({"message": "Evaluation updated"})
