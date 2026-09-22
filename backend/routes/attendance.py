from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
from db import db

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


def visible_employee_ids(claims):
    role = claims.get("role")
    if role == "EMPLOYEE":
        return [claims.get("employeeId")]
    if role == "MANAGER":
        return [x.get("employeeId") for x in db.employees.find({"department": claims.get("department")}, {"employeeId": 1, "_id": 0}) if x.get("employeeId")]
    return None


@attendance_bp.get("")
@jwt_required()
def list_attendance():
    claims = get_jwt()
    training_id = request.args.get("trainingId", "").strip()
    employee_ids = visible_employee_ids(claims)
    query = {}
    if training_id:
        query["trainingId"] = training_id
    if employee_ids is not None:
        query["employeeId"] = {"$in": employee_ids}

    records = list(db.training_participants.find(query, {"_id": 0}).limit(2000))
    for row in records:
        employee = db.employees.find_one({"employeeId": row.get("employeeId")}, {"_id": 0}) or {}
        try:
            training = db.trainings.find_one({"_id": ObjectId(row["trainingId"])}, {"_id": 0}) or {}
        except Exception:
            training = {}
        row["employeeName"] = employee.get("name", row.get("employeeId", ""))
        row["department"] = employee.get("department", "")
        row["trainingTitle"] = training.get("title", "")
        row["trainingDate"] = training.get("trainingDate")
        row["trainerName"] = training.get("trainerName", "")
        row["venue"] = training.get("venue", "")
    return jsonify(records)


@attendance_bp.get("/trainings")
@jwt_required()
def attendance_trainings():
    claims = get_jwt()
    employee_ids = visible_employee_ids(claims)
    query = {"status": {"$ne": "Cancelled"}}
    if employee_ids is not None:
        ids = db.training_participants.distinct("trainingId", {"employeeId": {"$in": employee_ids}})
        from bson import ObjectId
        query["_id"] = {"$in": [ObjectId(x) for x in ids if ObjectId.is_valid(x)]}
    rows = []
    for training in db.trainings.find(query).sort("trainingDate", 1):
        rows.append({
            "_id": str(training["_id"]),
            "title": training.get("title", ""),
            "trainingDate": training.get("trainingDate"),
            "trainerName": training.get("trainerName", ""),
            "venue": training.get("venue", ""),
            "durationMinutes": training.get("durationMinutes", 0),
            "status": training.get("status", "Upcoming"),
        })
    return jsonify(rows)


@attendance_bp.put("")
@jwt_required()
def update_attendance():
    claims = get_jwt()
    if claims.get("role") == "EMPLOYEE":
        return jsonify({"message": "Employees cannot edit attendance"}), 403
    payload = request.get_json(silent=True) or {}
    required = ["trainingId", "employeeId", "attendance"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return jsonify({"message": "Missing required fields", "fields": missing}), 400
    if payload["attendance"] not in {"Present", "Absent", "Partial"}:
        return jsonify({"message": "Invalid attendance value"}), 400
    employee = db.employees.find_one({"employeeId": payload["employeeId"]})
    if not employee:
        return jsonify({"message": "Employee not found"}), 404
    if claims.get("role") == "MANAGER" and employee.get("department") != claims.get("department"):
        return jsonify({"message": "Managers can only update attendance for their department"}), 403
    result = db.training_participants.update_one({"trainingId": payload["trainingId"], "employeeId": payload["employeeId"]}, {"$set": {"attendance": payload["attendance"], "updatedAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)}}, upsert=True)
    return jsonify({"message": "Attendance saved", "updated": result.modified_count > 0 or result.upserted_id is not None})


@attendance_bp.post("/bulk")
@jwt_required()
def bulk_attendance():
    claims = get_jwt()
    if claims.get("role") == "EMPLOYEE":
        return jsonify({"message": "Employees cannot edit attendance"}), 403
    payload = request.get_json(silent=True) or {}
    training_id = payload.get("trainingId")
    rows = payload.get("rows", [])
    if not training_id or not isinstance(rows, list):
        return jsonify({"message": "trainingId and rows are required"}), 400
    count = 0
    for row in rows:
        employee = db.employees.find_one({"employeeId": row.get("employeeId")})
        if not employee:
            continue
        if claims.get("role") == "MANAGER" and employee.get("department") != claims.get("department"):
            continue
        attendance = row.get("attendance", "Present")
        if attendance not in {"Present", "Absent", "Partial"}:
            continue
        db.training_participants.update_one({"trainingId": training_id, "employeeId": row.get("employeeId")}, {"$set": {"attendance": attendance}}, upsert=True)
        count += 1
    return jsonify({"message": "Attendance saved", "count": count})
