from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from db import db

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

def visible_employee_ids(claims):
    role = claims.get("role")
    if role == "EMPLOYEE":
        return [claims.get("employeeId")]
    if role == "MANAGER":
        return [x.get("employeeId") for x in db.employees.find({"department": claims.get("department")}, {"employeeId": 1, "_id": 0}) if x.get("employeeId")]
    return None

def can_mark_training(training, employee_id, claims):
    role = claims.get("role")
    if role == "HR_ADMIN":
        return True
    if role == "MANAGER":
        employee = db.employees.find_one({"employeeId": employee_id}, {"department": 1})
        return bool(employee and employee.get("department") == claims.get("department"))
    return role == "EMPLOYEE" and training.get("trainerEmployeeId") == claims.get("employeeId")

def enrich(rows):
    for row in rows:
        employee = db.employees.find_one({"employeeId": row.get("employeeId")}, {"_id": 0, "name": 1, "department": 1}) or {}
        try:
            training = db.trainings.find_one({"_id": ObjectId(row["trainingId"])}, {"_id": 0}) or {}
        except Exception:
            training = {}
        row["employeeName"] = employee.get("name", row.get("employeeId", ""))
        row["department"] = employee.get("department", "")
        row["trainingTitle"] = training.get("title", "")
        row["startDate"] = training.get("startDate", training.get("trainingDate"))
        row["endDate"] = training.get("endDate", training.get("startDate", training.get("trainingDate")))
        row["trainerName"] = training.get("trainerName", "")
        row["trainerEmployeeId"] = training.get("trainerEmployeeId", "")
        row["venue"] = training.get("venue", "")
    return rows

@attendance_bp.get("")
@jwt_required()
def list_attendance():
    claims = get_jwt()
    training_id = request.args.get("trainingId", "").strip()
    search = request.args.get("search", "").strip()
    start_date = request.args.get("startDate", "").strip()
    end_date = request.args.get("endDate", "").strip()
    employee_ids = visible_employee_ids(claims)
    query = {}
    if training_id:
        query["trainingId"] = training_id
    trainer_access = False
    if training_id and claims.get("role") == "EMPLOYEE" and ObjectId.is_valid(training_id):
        training = db.trainings.find_one({"_id": ObjectId(training_id)}, {"trainerEmployeeId": 1})
        trainer_access = bool(training and training.get("trainerEmployeeId") == claims.get("employeeId"))
    if employee_ids is not None and not trainer_access:
        query["employeeId"] = {"$in": employee_ids}
    records = enrich(list(db.training_participants.find(query, {"_id": 0}).limit(3000)))
    if search:
        q = search.lower()
        records = [r for r in records if q in f'{r.get("trainingTitle","")} {r.get("employeeName","")} {r.get("employeeId","")} {r.get("trainerName","")}'.lower()]
    if start_date:
        records = [r for r in records if str(r.get("startDate",""))[:10] >= start_date]
    if end_date:
        records = [r for r in records if str(r.get("endDate",""))[:10] <= end_date]
    return jsonify(records)

@attendance_bp.get("/trainings")
@jwt_required()
def attendance_trainings():
    claims = get_jwt()
    employee_ids = visible_employee_ids(claims)
    query = {"status": {"$ne": "Cancelled"}}
    if claims.get("role") == "EMPLOYEE":
        assigned = db.training_participants.distinct("trainingId", {"employeeId": claims.get("employeeId")})
        trainer_ids = [str(x["_id"]) for x in db.trainings.find({"trainerEmployeeId": claims.get("employeeId")}, {"_id": 1})]
        ids = set(assigned + trainer_ids)
        query["_id"] = {"$in": [ObjectId(x) for x in ids if ObjectId.is_valid(x)]}
    elif employee_ids is not None:
        ids = db.training_participants.distinct("trainingId", {"employeeId": {"$in": employee_ids}})
        query["_id"] = {"$in": [ObjectId(x) for x in ids if ObjectId.is_valid(x)]}
    rows = []
    for training in db.trainings.find(query).sort("startDate", 1):
        rows.append({
            "_id": str(training["_id"]),
            "title": training.get("title", ""),
            "startDate": training.get("startDate", training.get("trainingDate")),
            "endDate": training.get("endDate", training.get("startDate", training.get("trainingDate"))),
            "trainingDate": training.get("startDate", training.get("trainingDate")),
            "trainerName": training.get("trainerName", ""),
            "trainerEmployeeId": training.get("trainerEmployeeId", ""),
            "venue": training.get("venue", ""),
            "status": training.get("status", "Upcoming"),
        })
    return jsonify(rows)

@attendance_bp.put("")
@jwt_required()
def update_attendance():
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}
    required = ["trainingId", "employeeId", "attendance"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return jsonify({"message": "Missing required fields", "fields": missing}), 400
    if payload["attendance"] not in {"Present", "Absent", "Partial"}:
        return jsonify({"message": "Invalid attendance value"}), 400
    training = db.trainings.find_one({"_id": ObjectId(payload["trainingId"])}) if ObjectId.is_valid(payload["trainingId"]) else None
    if not training:
        return jsonify({"message": "Training not found"}), 404
    if not can_mark_training(training, payload["employeeId"], claims):
        return jsonify({"message": "Only the assigned trainer, HR Admin, or the employee's department manager can mark attendance"}), 403
    participant = db.training_participants.find_one({"trainingId": payload["trainingId"], "employeeId": payload["employeeId"]})
    if not participant:
        return jsonify({"message": "Employee is not assigned to this training"}), 404
    db.training_participants.update_one({"_id": participant["_id"]}, {"$set": {"attendance": payload["attendance"], "attendanceMarkedBy": claims.get("employeeId"), "attendanceMarkedAt": datetime.now(timezone.utc), "updatedAt": datetime.now(timezone.utc)}})
    return jsonify({"message": "Attendance saved"})

@attendance_bp.post("/bulk")
@jwt_required()
def bulk_attendance():
    claims = get_jwt()
    payload = request.get_json(silent=True) or {}
    training_id = str(payload.get("trainingId", ""))
    rows = payload.get("rows", [])
    if not training_id or not isinstance(rows, list):
        return jsonify({"message": "trainingId and rows are required"}), 400
    training = db.trainings.find_one({"_id": ObjectId(training_id)}) if ObjectId.is_valid(training_id) else None
    if not training:
        return jsonify({"message": "Training not found"}), 404
    if claims.get("role") == "EMPLOYEE" and training.get("trainerEmployeeId") != claims.get("employeeId"):
        return jsonify({"message": "Only the assigned trainer can mark trainee attendance"}), 403
    count = 0
    for row in rows:
        eid = row.get("employeeId")
        if row.get("attendance") not in {"Present", "Absent", "Partial"}:
            continue
        participant = db.training_participants.find_one({"trainingId": training_id, "employeeId": eid})
        if not participant or not can_mark_training(training, eid, claims):
            continue
        db.training_participants.update_one({"_id": participant["_id"]}, {"$set": {"attendance": row["attendance"], "attendanceMarkedBy": claims.get("employeeId"), "attendanceMarkedAt": datetime.now(timezone.utc), "updatedAt": datetime.now(timezone.utc)}})
        count += 1
    return jsonify({"message": "Attendance saved", "count": count})
