from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from flask_jwt_extended import jwt_required, get_jwt
from db import db
from models.employee import build_employee, serialize_employee

employees_bp = Blueprint("employees", __name__, url_prefix="/api/employees")

@employees_bp.get("")
@jwt_required()
def list_employees():
    claims = get_jwt()
    department = request.args.get("department")
    if claims.get("role") == "MANAGER":
        department = claims.get("department")
    query = {"department": department} if department else {}
    records = [serialize_employee(x) for x in db.employees.find(query).sort("name", 1)]
    return jsonify(records)

@employees_bp.post("")
@jwt_required()
def create_employee():
    if get_jwt().get("role") != "HR_ADMIN":
        return jsonify({"message": "HR Admin permission required"}), 403

    payload = request.get_json(silent=True) or {}
    required = ["employeeId", "name", "department", "designation", "password"]
    missing = [x for x in required if not str(payload.get(x, "")).strip()]
    if missing:
        return jsonify({"message": "Employee ID, name, department, designation and password are required", "fields": missing}), 400

    employee_id = str(payload["employeeId"]).strip().upper()
    password = str(payload["password"])
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400

    if db.employees.find_one({"employeeId": employee_id}) or db.users.find_one({"username": employee_id.lower()}):
        return jsonify({"message": "Employee ID already exists"}), 409

    employee = build_employee({**payload, "employeeId": employee_id})
    user = {
        "username": employee_id.lower(),
        "name": employee["name"],
        "passwordHash": generate_password_hash(password),
        "role": "EMPLOYEE",
        "employeeId": employee_id,
        "department": employee["department"],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }

    try:
        db.employees.insert_one(employee)
        db.users.insert_one(user)
    except Exception:
        db.employees.delete_one({"employeeId": employee_id})
        return jsonify({"message": "Unable to create employee account"}), 500

    return jsonify({
        "message": "Employee and login credentials created",
        "employeeId": employee_id,
    }), 201


@employees_bp.put("/<employee_id>/credentials")
@jwt_required()
def set_employee_credentials(employee_id):
    if get_jwt().get("role") != "HR_ADMIN":
        return jsonify({"message": "HR Admin permission required"}), 403

    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password", ""))
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400

    employee = db.employees.find_one({"employeeId": employee_id.upper()})
    if not employee:
        return jsonify({"message": "Employee not found"}), 404

    now = datetime.now(timezone.utc)
    user = db.users.find_one({"employeeId": employee_id.upper()})
    if user:
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "passwordHash": generate_password_hash(password),
                "name": employee.get("name", ""),
                "department": employee.get("department", ""),
                "updatedAt": now,
            }},
        )
    else:
        db.users.insert_one({
            "username": employee_id.lower(),
            "name": employee.get("name", ""),
            "passwordHash": generate_password_hash(password),
            "role": "EMPLOYEE",
            "employeeId": employee_id.upper(),
            "department": employee.get("department", ""),
            "createdAt": now,
            "updatedAt": now,
        })

    return jsonify({"message": "Employee credentials saved"})


@employees_bp.put("/<employee_id>")
@jwt_required()
def update_employee(employee_id):
    if get_jwt().get("role") != "HR_ADMIN":
        return jsonify({"message": "HR Admin permission required"}), 403
    from bson import ObjectId
    payload = request.get_json(silent=True) or {}
    allowed = ["name", "department", "designation", "reportingManager", "email", "status"]
    updates = {k: payload[k] for k in allowed if k in payload}
    try:
        result = db.employees.update_one({"_id": ObjectId(employee_id)}, {"$set": updates})
    except Exception:
        return jsonify({"message": "Invalid employee id"}), 400
    if result.matched_count == 0:
        return jsonify({"message": "Employee not found"}), 404

    employee = db.employees.find_one({"_id": ObjectId(employee_id)})
    if employee:
        db.users.update_one(
            {"employeeId": employee.get("employeeId")},
            {"$set": {
                "name": employee.get("name", ""),
                "department": employee.get("department", ""),
                "updatedAt": datetime.now(timezone.utc),
            }},
        )
    return jsonify({"message": "Employee updated"})
