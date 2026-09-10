from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from db import db
from models.training import build_training, serialize_training
from bson import ObjectId
from datetime import datetime, timezone

trainings_bp = Blueprint("trainings", __name__, url_prefix="/api/trainings")

@trainings_bp.get("")
@jwt_required()
def list_trainings():
    claims = get_jwt(); status = request.args.get("status")
    query = {"status": status} if status else {}
    if claims.get("role") == "EMPLOYEE": query["traineeIds"] = claims.get("employeeId")
    elif claims.get("role") == "MANAGER": query["departments"] = claims.get("department")
    records = [serialize_training(x) for x in db.trainings.find(query).sort("trainingDate", 1)]
    return jsonify(records)

@trainings_bp.get("/<training_id>")
@jwt_required()
def get_training(training_id):
    try:
        doc = db.trainings.find_one({"_id": ObjectId(training_id)})
    except Exception:
        return jsonify({"message": "Invalid training id"}), 400
    if not doc:
        return jsonify({"message": "Training not found"}), 404
    role = get_jwt().get("role")
    if role == "EMPLOYEE" and get_jwt().get("employeeId") not in doc.get("traineeIds", []):
        return jsonify({"message": "Training not available"}), 403
    if role == "MANAGER" and get_jwt().get("department") not in doc.get("departments", []):
        return jsonify({"message": "Training not available"}), 403
    return jsonify(serialize_training(doc))

@trainings_bp.get("/progress")
@jwt_required()
def training_progress():
    """Live-friendly progress feed. Frontend polls this endpoint every few seconds."""
    claims = get_jwt()
    role = claims.get("role")
    query = {}

    if role == "EMPLOYEE":
        query["employeeId"] = claims.get("employeeId")
    elif role == "MANAGER":
        ids = [e.get("employeeId") for e in db.employees.find(
            {"department": claims.get("department"), "status": "Active"},
            {"employeeId": 1}
        )]
        query["employeeId"] = {"$in": ids}

    participants = list(db.training_participants.find(query).sort("updatedAt", -1))
    result = []
    for p in participants:
        training = None
        try:
            training = db.trainings.find_one({"_id": ObjectId(p.get("trainingId"))})
        except Exception:
            pass
        employee = db.employees.find_one({"employeeId": p.get("employeeId")}) or {}
        if not training:
            continue
        result.append({
            "trainingId": p.get("trainingId"),
            "trainingTitle": training.get("title", ""),
            "employeeId": p.get("employeeId"),
            "employeeName": employee.get("name", p.get("employeeId", "")),
            "department": employee.get("department", ""),
            "attendance": p.get("attendance", "Pending"),
            "completionStatus": p.get("completionStatus", "Assigned"),
            "feedbackStatus": p.get("feedbackStatus", "Pending"),
            "updatedAt": p.get("updatedAt").isoformat() if p.get("updatedAt") else None,
        })

    return jsonify(result)


@trainings_bp.put("/<training_id>/progress")
@jwt_required()
def update_training_progress(training_id):
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}
    status = payload.get("completionStatus")

    if status not in {"Assigned", "In Progress", "Completed"}:
        return jsonify({"message": "Invalid completion status"}), 400

    try:
        training = db.trainings.find_one({"_id": ObjectId(training_id)})
    except Exception:
        return jsonify({"message": "Invalid training id"}), 400
    if not training:
        return jsonify({"message": "Training not found"}), 404

    employee_id = payload.get("employeeId")
    if claims.get("role") == "EMPLOYEE":
        employee_id = claims.get("employeeId")
    elif claims.get("role") == "MANAGER":
        employee = db.employees.find_one({"employeeId": employee_id})
        if not employee or employee.get("department") != claims.get("department"):
            return jsonify({"message": "Managers can only update their department"}), 403
    elif claims.get("role") != "HR_ADMIN":
        return jsonify({"message": "Permission denied"}), 403

    if not employee_id or employee_id not in training.get("traineeIds", []):
        return jsonify({"message": "Employee is not assigned to this training"}), 400

    now = datetime.now(timezone.utc)
    db.training_participants.update_one(
        {"trainingId": training_id, "employeeId": employee_id},
        {"$set": {"completionStatus": status, "updatedAt": now},
         "$setOnInsert": {"attendance": "Pending", "feedbackStatus": "Pending", "updatedAt": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return jsonify({"message": "Progress updated", "completionStatus": status})


@trainings_bp.post("")
@jwt_required()
def create_training():
    if get_jwt().get("role") not in {"HR_ADMIN", "MANAGER"}: return jsonify({"message": "Manager or HR Admin permission required"}), 403
    payload = request.get_json(silent=True) or {}
    if not payload.get("title"):
        return jsonify({"message": "Training title is required"}), 400
    claims = get_jwt()
    if claims.get("role") == "MANAGER":
        departments = payload.get("departments") or []
        if isinstance(departments, str): departments = [departments]
        if any(d != claims.get("department") for d in departments):
            return jsonify({"message": "Managers can only create training for their department"}), 403
    doc = build_training(payload)
    result = db.trainings.insert_one(doc)

    # Create one participant record per assigned employee.
    for employee_id in doc["traineeIds"]:
        db.training_participants.update_one(
            {"trainingId": str(result.inserted_id), "employeeId": employee_id},
            {"$setOnInsert": {
                "trainingId": str(result.inserted_id),
                "employeeId": employee_id,
                "attendance": "Pending",
                "completionStatus": "Assigned",
                "feedbackStatus": "Pending",
                "updatedAt": datetime.now(timezone.utc),
            }},
            upsert=True,
        )

    return jsonify({"message": "Training created", "id": str(result.inserted_id)}), 201

@trainings_bp.put("/<training_id>")
@jwt_required()
def update_training(training_id):
    claims = get_jwt()
    if claims.get("role") not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "Manager or HR Admin permission required"}), 403
    payload = request.get_json(silent=True) or {}
    allowed = [
        "title", "content", "trainingType", "trainerName", "trainerCategory",
        "venue", "departments", "traineeIds", "trainingDate", "trainingMode",
        "durationMinutes", "status"
    ]
    updates = {k: payload[k] for k in allowed if k in payload}
    if not updates:
        return jsonify({"message": "No fields to update"}), 400
    try:
        existing = db.trainings.find_one({"_id": ObjectId(training_id)})
    except Exception:
        return jsonify({"message": "Invalid training id"}), 400
    if not existing:
        return jsonify({"message": "Training not found"}), 404
    if claims.get("role") == "MANAGER":
        if claims.get("department") not in existing.get("departments", []):
            return jsonify({"message": "Managers can only update training for their department"}), 403
        if "departments" in updates and any(d != claims.get("department") for d in (updates["departments"] or [])):
            return jsonify({"message": "Managers can only use their department"}), 403
    result = db.trainings.update_one({"_id": ObjectId(training_id)}, {"$set": updates})
    return jsonify({"message": "Training updated"})

@trainings_bp.delete("/<training_id>")
@jwt_required()
def delete_training(training_id):
    claims = get_jwt()
    if claims.get("role") not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "Manager or HR Admin permission required"}), 403
    try:
        existing = db.trainings.find_one({"_id": ObjectId(training_id)})
    except Exception:
        return jsonify({"message": "Invalid training id"}), 400
    if not existing:
        return jsonify({"message": "Training not found"}), 404
    if claims.get("role") == "MANAGER" and claims.get("department") not in existing.get("departments", []):
        return jsonify({"message": "Managers can only delete training for their department"}), 403
    result = db.trainings.delete_one({"_id": ObjectId(training_id)})
    if result.deleted_count == 0:
        return jsonify({"message": "Training not found"}), 404
    db.training_participants.delete_many({"trainingId": training_id})
    return jsonify({"message": "Training deleted"})


@trainings_bp.post("/<training_id>/complete")
@jwt_required()
def complete_training(training_id):
    from datetime import datetime, timezone
    claims = get_jwt()
    if claims.get("role") not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "Manager or HR Admin permission required"}), 403
    try:
        existing = db.trainings.find_one({"_id": ObjectId(training_id)})
    except Exception:
        return jsonify({"message": "Invalid training id"}), 400
    if not existing:
        return jsonify({"message": "Training not found"}), 404
    if claims.get("role") == "MANAGER" and claims.get("department") not in existing.get("departments", []):
        return jsonify({"message": "Managers can only complete training for their department"}), 403
    completed_at = datetime.now(timezone.utc)
    db.trainings.update_one({"_id": ObjectId(training_id)}, {"$set": {"status": "Completed", "completedAt": completed_at}})
    db.training_participants.update_many({"trainingId": training_id}, {"$set": {"completionStatus": "Completed"}})
    return jsonify({"message": "Training marked completed"})


@trainings_bp.get("/<training_id>/participants")
@jwt_required()
def list_participants(training_id):
    claims = get_jwt()
    if claims.get("role") not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "Manager or HR Admin permission required"}), 403
    training = db.trainings.find_one({"_id": ObjectId(training_id)})
    if not training:
        return jsonify({"message": "Training not found"}), 404
    if claims.get("role") == "MANAGER" and claims.get("department") not in training.get("departments", []):
        return jsonify({"message": "Managers can only view their department training"}), 403
    participants = []
    for item in db.training_participants.find({"trainingId": training_id}):
        emp = db.employees.find_one({"employeeId": item.get("employeeId")}) or {}
        participants.append({
            "employeeId": item.get("employeeId"),
            "name": emp.get("name", item.get("employeeId")),
            "department": emp.get("department", ""),
            "designation": emp.get("designation", ""),
            "attendance": item.get("attendance", "Pending"),
            "feedbackStatus": item.get("feedbackStatus", "Pending"),
        })
    return jsonify(participants)

@trainings_bp.put("/<training_id>/participants")
@jwt_required()
def replace_participants(training_id):
    claims = get_jwt()
    if claims.get("role") not in {"HR_ADMIN", "MANAGER"}:
        return jsonify({"message": "Manager or HR Admin permission required"}), 403
    payload = request.get_json(silent=True) or {}
    employee_ids = list(dict.fromkeys(payload.get("employeeIds", [])))
    training = db.trainings.find_one({"_id": ObjectId(training_id)})
    if not training:
        return jsonify({"message": "Training not found"}), 404
    if claims.get("role") == "MANAGER" and claims.get("department") not in training.get("departments", []):
        return jsonify({"message": "Managers can only manage their department training"}), 403
    if claims.get("role") == "MANAGER":
        allowed = {e.get("employeeId") for e in db.employees.find({"department": claims.get("department")})}
        if any(eid not in allowed for eid in employee_ids):
            return jsonify({"message": "Managers can only assign employees from their department"}), 403
    db.trainings.update_one({"_id": ObjectId(training_id)}, {"$set": {"traineeIds": employee_ids}})
    for eid in employee_ids:
        db.training_participants.update_one(
            {"trainingId": training_id, "employeeId": eid},
            {"$setOnInsert": {"trainingId": training_id, "employeeId": eid, "attendance": "Pending", "completionStatus": "Assigned", "feedbackStatus": "Pending", "updatedAt": datetime.now(timezone.utc)}},
            upsert=True,
        )
    db.training_participants.delete_many({"trainingId": training_id, "employeeId": {"$nin": employee_ids}})
    return jsonify({"message": "Participants updated", "count": len(employee_ids)})
