
import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.errors import DuplicateKeyError

from db import db
from models.user import serialize_user, build_user
from config import Config
from email_service import send_verification_code

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def ensure_admin_user():
    if not Config.ADMIN_PASSWORD:
        return
    existing = db.users.find_one({"username": Config.ADMIN_EMPLOYEE_ID.lower()})
    if existing:
        return
    now = datetime.now(timezone.utc)
    user = build_user(
        Config.ADMIN_EMPLOYEE_ID, Config.ADMIN_NAME, Config.ADMIN_PASSWORD,
        "HR_ADMIN", Config.ADMIN_EMPLOYEE_ID, Config.ADMIN_DEPARTMENT,
    )
    employee = {
        "employeeId": Config.ADMIN_EMPLOYEE_ID,
        "name": Config.ADMIN_NAME,
        "department": Config.ADMIN_DEPARTMENT,
        "designation": "HR Administrator",
        "reportingManager": "",
        "email": Config.ADMIN_EMAIL,
        "status": "Active",
        "createdAt": now,
        "updatedAt": now,
    }
    try:
        db.employees.update_one({"employeeId": Config.ADMIN_EMPLOYEE_ID},
                                {"$setOnInsert": employee}, upsert=True)
        db.users.insert_one(user)
    except DuplicateKeyError:
        pass


def _signup_payload(payload):
    required = ["employeeId", "name", "email", "password", "department", "designation", "role"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return None, (jsonify({"message": "Please fill all required fields", "fields": missing}), 400)

    employee_id = str(payload["employeeId"]).strip().upper()
    name = str(payload["name"]).strip()
    email = str(payload["email"]).strip().lower()
    password = str(payload["password"])
    department = str(payload["department"]).strip()
    designation = str(payload["designation"]).strip()
    requested_role = str(payload["role"]).strip().upper()
    role = {"ADMIN": "HR_ADMIN", "HR_ADMIN": "HR_ADMIN", "MANAGER": "MANAGER", "EMPLOYEE": "EMPLOYEE"}.get(requested_role)

    if role is None:
        return None, (jsonify({"message": "Role must be Admin, Manager or Employee"}), 400)
    if len(password) < 8:
        return None, (jsonify({"message": "Password must be at least 8 characters"}), 400)
    if "@" not in email:
        return None, (jsonify({"message": "Please enter a valid email address"}), 400)

    from routes.departments import DEPARTMENTS
    if department not in DEPARTMENTS:
        return None, (jsonify({"message": "Please select a valid department"}), 400)

    if db.users.find_one({"username": employee_id.lower()}) or db.employees.find_one({"employeeId": employee_id}):
        return None, (jsonify({"message": "Employee ID is already registered"}), 409)
    if db.employees.find_one({"email": email}):
        return None, (jsonify({"message": "Email address is already registered"}), 409)

    return {
        "employeeId": employee_id, "name": name, "email": email, "password": password,
        "department": department, "designation": designation,
        "reportingManager": str(payload.get("reportingManager", "")).strip(), "role": role,
    }, None


@auth_bp.post("/signup/request-code")
def request_signup_code():
    payload, error = _signup_payload(request.get_json(silent=True) or {})
    if error:
        return error

    code = f"{secrets.randbelow(1000000):06d}"
    now = datetime.now(timezone.utc)
    db.signup_verifications.delete_many({"email": payload["email"]})
    db.signup_verifications.insert_one({
        "email": payload["email"],
        "employeeId": payload["employeeId"],
        "codeHash": generate_password_hash(code),
        "payload": payload,
        "createdAt": now,
        "expiresAt": now + timedelta(minutes=Config.VERIFICATION_CODE_EXPIRES_MINUTES),
        "attempts": 0,
    })

    if not send_verification_code(payload["email"], code):
        db.signup_verifications.delete_many({"email": payload["email"]})
        return jsonify({"message": "Unable to send verification email. Please check the email/SMTP configuration."}), 503

    return jsonify({"message": "Verification code sent to your email.", "email": payload["email"]}), 200


@auth_bp.post("/signup/verify")
def verify_signup():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    code = str(payload.get("code", "")).strip()

    if not email or not code:
        return jsonify({"message": "Email and 6-digit verification code are required"}), 400
    if len(code) != 6 or not code.isdigit():
        return jsonify({"message": "Verification code must contain 6 digits"}), 400

    verification = db.signup_verifications.find_one({"email": email})
    if not verification:
        return jsonify({"message": "Verification code not found. Request a new code."}), 400

    now = datetime.now(timezone.utc)
    expires = verification.get("expiresAt")
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires and expires < now:
        db.signup_verifications.delete_one({"_id": verification["_id"]})
        return jsonify({"message": "Verification code has expired. Request a new code."}), 400

    attempts = int(verification.get("attempts", 0))
    if attempts >= 5:
        db.signup_verifications.delete_one({"_id": verification["_id"]})
        return jsonify({"message": "Too many incorrect attempts. Request a new code."}), 429

    if not check_password_hash(verification.get("codeHash", ""), code):
        db.signup_verifications.update_one({"_id": verification["_id"]}, {"$inc": {"attempts": 1}})
        return jsonify({"message": "Incorrect verification code"}), 400

    data = verification["payload"]
    employee_id = data["employeeId"]
    if db.users.find_one({"username": employee_id.lower()}) or db.employees.find_one({"employeeId": employee_id}):
        db.signup_verifications.delete_one({"_id": verification["_id"]})
        return jsonify({"message": "Employee ID is already registered"}), 409

    now = datetime.now(timezone.utc)
    employee = {
        "employeeId": employee_id, "name": data["name"], "department": data["department"],
        "designation": data["designation"], "reportingManager": data.get("reportingManager", ""),
        "email": data["email"], "status": "Active", "createdAt": now, "updatedAt": now,
        "registeredBy": "SELF", "accountRole": data["role"],
    }
    user = build_user(employee_id, data["name"], data["password"], data["role"], employee_id, data["department"])

    try:
        db.employees.insert_one(employee)
        db.users.insert_one(user)
        db.signup_verifications.delete_one({"_id": verification["_id"]})
    except DuplicateKeyError:
        db.employees.delete_one({"employeeId": employee_id, "registeredBy": "SELF"})
        return jsonify({"message": "Employee ID is already registered"}), 409
    except Exception as exc:
        print("VERIFY SIGNUP ERROR:", exc)
        db.employees.delete_one({"employeeId": employee_id, "registeredBy": "SELF"})
        return jsonify({"message": "Unable to complete signup"}), 500

    return jsonify({"message": "Email verified and signup completed successfully.", "employeeId": employee_id, "role": data["role"]}), 201


@auth_bp.post("/signup")
def signup_legacy():
    return jsonify({"message": "Email verification is required. Use the signup verification flow."}), 400


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

    employee = db.employees.find_one({"employeeId": user.get("employeeId")})
    if employee and employee.get("status", "Active") != "Active":
        return jsonify({"message": "This employee account is inactive"}), 403

    token = create_access_token(
        identity=str(user["_id"]),
        additional_claims={
            "role": user["role"], "employeeId": user.get("employeeId"),
            "department": user.get("department"), "name": user.get("name"),
        },
    )
    return jsonify({"accessToken": token, "expiresIn": Config.JWT_ACCESS_TOKEN_EXPIRES, "user": serialize_user(user)})


@auth_bp.get("/me")
@jwt_required()
def me():
    from bson import ObjectId
    try:
        user = db.users.find_one({"_id": ObjectId(get_jwt().get("sub"))})
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
    db.users.update_one({"_id": user["_id"]}, {"$set": {"passwordHash": generate_password_hash(new_password), "updatedAt": datetime.now(timezone.utc)}})
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
