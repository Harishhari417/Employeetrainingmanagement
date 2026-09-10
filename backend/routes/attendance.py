from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from db import db
from bson import ObjectId

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

@attendance_bp.get("")
@jwt_required()
def list_attendance():
    claims = get_jwt()
    training_id = request.args.get("trainingId")
    query = {"trainingId": training_id} if training_id else {}
    if claims.get("role") == "EMPLOYEE":
        query["employeeId"] = claims.get("employeeId")
    elif claims.get("role") == "MANAGER":
        # Department filtering is applied after joining employee data below.
        pass
    records = list(db.training_participants.find(query, {"_id": 0}).limit(1000))
    for row in records:
        employee = db.employees.find_one({"employeeId": row.get("employeeId")}, {"_id": 0}) or {}
        training = db.trainings.find_one({"_id": ObjectId(row["trainingId"])}, {"_id": 0}) if row.get("trainingId") else None
        row["employeeName"] = employee.get("name", row.get("employeeId", ""))
        row["department"] = employee.get("department", "")
        row["trainingTitle"] = (training or {}).get("title", "")
    if claims.get("role") == "MANAGER":
        records = [r for r in records if r.get("department") == claims.get("department")]
    return jsonify(records)

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
    if claims.get("role") == "MANAGER" and (not employee or employee.get("department") != claims.get("department")):
        return jsonify({"message": "Managers can only update attendance for their department"}), 403
    result = db.training_participants.update_one(
        {"trainingId": payload["trainingId"], "employeeId": payload["employeeId"]},
        {"$set": {"attendance": payload["attendance"]}},
        upsert=True,
    )
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
    for row in rows:
        employee = db.employees.find_one({"employeeId": row.get("employeeId")})
        if claims.get("role") == "MANAGER" and (not employee or employee.get("department") != claims.get("department")):
            continue
        db.training_participants.update_one(
            {"trainingId": training_id, "employeeId": row.get("employeeId")},
            {"$set": {"attendance": row.get("attendance", "Present")}},
            upsert=True,
        )
    return jsonify({"message": "Attendance saved", "count": len(rows)})
