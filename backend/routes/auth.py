from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.errors import DuplicateKeyError

from db import db
from models.user import serialize_user, build_user
from config import ADMIN_EMPLOYEE_ID, ADMIN_PASSWORD, ADMIN_NAME, ADMIN_DEPARTMENT

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth/login")


def ensure_admin_user():
    """Create the initial HR account only when ADMIN_PASSWORD is configured."""
    if not ADMIN_PASSWORD:
        return
    existing = db.users.find_one({"username": ADMIN_EMPLOYEE_ID.lower()})
    if existing:
        return
    now = datetime.now(timezone.utc)
    user = build_user(
        ADMIN_EMPLOYEE_ID,
        ADMIN_NAME,
        ADMIN_PASSWORD,
        "HR_ADMIN",
        ADMIN_EMPLOYEE_ID,
        ADMIN_DEPARTMENT,
    )
    employee = {
        "employeeId": ADMIN_EMPLOYEE_ID,
        "name": ADMIN_NAME,
        "department": ADMIN_DEPARTMENT,
        "designation": "HR Administrator",
        "reportingManager": "",
        "email": "",
        "status": "Active",
        "createdAt": now,
        "updatedAt": now,
    }
    try:
        db.employees.update_one(
            {"employeeId": ADMIN_EMPLOYEE_ID},
            {"$setOnInsert": employee},
            upsert=True,
        )
        db.users.insert_one(user)
    except DuplicateKeyError:
        pass


@auth_bp.post("/signup")
def signup():
    payload = request.get_json(silent=True) or {}

    required = [
        "employeeId",
        "name",
        "email",
        "password",
        "department",
        "designation",
    ]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return jsonify({"message": "Please fill all required fields", "fields": missing}), 400

    employee_id = str(payload["employeeId"]).strip().upper()
    name = str(payload["name"]).strip()
    email = str(payload["email"]).strip().lower()
    password = str(payload["password"])
    department = str(payload["department"]).strip()
    designation = str(payload["designation"]).strip()
    reporting_manager = str(payload.get("reportingManager", "")).strip()

    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400

    if db.users.find_one({"username": employee_id.lower()}):
        return jsonify({"message": "Employee ID is already registered"}), 409

    if db.employees.find_one({"employeeId": employee_id}):
        return jsonify({
            "message": "Employee ID already exists. If HR created this employee, ask HR to provide the credentials."
        }), 409

    now = datetime.now(timezone.utc)
    employee = {
        "employeeId": employee_id,
        "name": name,
        "department": department,
        "designation": designation,
        "reportingManager": reporting_manager,
        "email": email,
        "status": "Active",
        "createdAt": now,
        "updatedAt": now,
        "registeredBy": "SELF",
    }

    user = build_user(
        employee_id,
        name,
        password,
        "EMPLOYEE",
        employee_id,
        department,
    )

    try:
        db.employees.insert_one(employee)
        db.users.insert_one(user)
    except DuplicateKeyError:
        db.employees.delete_one({"employeeId": employee_id, "registeredBy": "SELF"})
        return jsonify({"message": "Employee ID is already registered"}), 409
    except Exception as exc:
        db.employees.delete_one({"employeeId": employee_id, "registeredBy": "SELF"})
        return jsonify({"message": "Unable to complete signup"}), 500

    return jsonify({
        "message": "Signup successful. You can now sign in with your Employee ID and password.",
        "employeeId": employee_id,
    }), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not username or not password:
        return jsonify({"message": "Employee ID and password are required"}), 400

    user = db.users.find_one({"username": username})

    if not user or not check_password_hash(user.get("passwordHash", ""), password):
        return jsonify({"message": "Invalid Employee ID or password"}), 401

    if user.get("role") == "EMPLOYEE":
        employee = db.employees.find_one({"employeeId": user.get("employeeId")})
        if not employee or employee.get("status", "Active") != "Active":
            return jsonify({"message": "This employee account is inactive"}), 403

    token = create_access_token(
        identity=str(user["_id"]),
        additional_claims={
            "role": user["role"],
            "employeeId": user.get("employeeId"),
            "department": user.get("department"),
        },
    )

    return jsonify({
        "accessToken": token,
        "user": serialize_user(user),
    })


@auth_bp.get("/me")
@jwt_required()
def me():
    from bson import ObjectId
    user_id = get_jwt().get("sub")
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = None

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify(serialize_user(user))


@auth_bp.put("/password")
@jwt_required()
def change_password():
    payload = request.get_json(silent=True) or {}
    current = str(payload.get("currentPassword", ""))
    new_password = str(payload.get("newPassword", ""))

    if not current or not new_password:
        return jsonify({"message": "Current password and new password are required"}), 400
    if len(new_password) < 8:
        return jsonify({"message": "New password must be at least 8 characters"}), 400

    from bson import ObjectId
    try:
        user = db.users.find_one({"_id": ObjectId(get_jwt().get("sub"))})
    except Exception:
        user = None

    if not user or not check_password_hash(user.get("passwordHash", ""), current):
        return jsonify({"message": "Current password is incorrect"}), 401

    db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "passwordHash": generate_password_hash(new_password),
                "updatedAt": datetime.now(timezone.utc),
            }
        },
    )
    return jsonify({"message": "Password changed successfully. Please sign in again."})


@auth_bp.post("/logout")
@jwt_required()
def logout():
    return jsonify({"message": "Logged out"})


def role_required(*roles):
    claims = get_jwt()
    if claims.get("role") not in roles:
        return jsonify({"message": "You do not have permission for this resource"}), 403
    return None
