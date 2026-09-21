from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
from db import db
from models.employee import build_employee, serialize_employee

employees_bp = Blueprint("employees", __name__, url_prefix="/api/employees")


def is_hr_admin():
    return get_jwt().get("role") == "HR_ADMIN"


def now_utc():
    return datetime.now(timezone.utc)


@employees_bp.get("")
@jwt_required()
def list_employees():
    claims = get_jwt()
    department = request.args.get("department", "").strip()

    if claims.get("role") == "MANAGER":
        department = claims.get("department", "")

    query = {}

    if department:
        query["department"] = department

    records = [
        serialize_employee(employee)
        for employee in db.employees.find(query).sort("name", 1)
    ]

    return jsonify(records), 200


@employees_bp.post("")
@jwt_required()
def create_employee():
    if not is_hr_admin():
        return jsonify({"message": "HR Admin permission required"}), 403

    payload = request.get_json(silent=True) or {}

    required = [
        "employeeId",
        "name",
        "department",
        "designation",
        "password",
    ]

    missing = [
        field
        for field in required
        if not str(payload.get(field, "")).strip()
    ]

    if missing:
        return jsonify({
            "message": "Employee ID, name, department, designation and password are required",
            "fields": missing
        }), 400

    employee_id = str(payload["employeeId"]).strip().upper()
    password = str(payload["password"])

    if len(password) < 8:
        return jsonify({
            "message": "Password must be at least 8 characters"
        }), 400

    existing_employee = db.employees.find_one({
        "employeeId": employee_id
    })

    existing_user = db.users.find_one({
        "username": employee_id.lower()
    })

    if existing_employee or existing_user:
        return jsonify({
            "message": "Employee ID already exists"
        }), 409

    try:
        employee = build_employee({
            **payload,
            "employeeId": employee_id,
            "status": payload.get("status", "Active")
        })

        user = {
            "username": employee_id.lower(),
            "name": employee.get("name", ""),
            "passwordHash": generate_password_hash(password),
            "role": "EMPLOYEE",
            "employeeId": employee_id,
            "department": employee.get("department", ""),
            "createdAt": now_utc(),
            "updatedAt": now_utc(),
        }

        employee_result = db.employees.insert_one(employee)

        try:
            db.users.insert_one(user)
        except Exception:
            db.employees.delete_one({
                "_id": employee_result.inserted_id
            })
            raise

        created_employee = db.employees.find_one({
            "_id": employee_result.inserted_id
        })

        return jsonify({
            "message": "Employee and login credentials created",
            "employee": serialize_employee(created_employee),
            "employeeId": employee_id
        }), 201

    except Exception as error:
        print("CREATE EMPLOYEE ERROR:", error)

        return jsonify({
            "message": "Unable to create employee account"
        }), 500


@employees_bp.put("/<employee_id>")
@jwt_required()
def update_employee(employee_id):
    if not is_hr_admin():
        return jsonify({
            "message": "HR Admin permission required"
        }), 403

    try:
        object_id = ObjectId(employee_id)
    except Exception:
        return jsonify({
            "message": "Invalid employee id"
        }), 400

    existing = db.employees.find_one({
        "_id": object_id
    })

    if not existing:
        return jsonify({
            "message": "Employee not found"
        }), 404

    payload = request.get_json(silent=True) or {}

    allowed = [
        "name",
        "department",
        "designation",
        "reportingManager",
        "email",
        "status"
    ]

    updates = {}

    for field in allowed:
        if field in payload:
            if isinstance(payload[field], str):
                updates[field] = payload[field].strip()
            else:
                updates[field] = payload[field]

    if "employeeId" in payload:
        new_employee_id = str(
            payload.get("employeeId", "")
        ).strip().upper()

        if not new_employee_id:
            return jsonify({
                "message": "Employee ID cannot be empty"
            }), 400

        duplicate = db.employees.find_one({
            "employeeId": new_employee_id,
            "_id": {
                "$ne": object_id
            }
        })

        if duplicate:
            return jsonify({
                "message": "Employee ID already exists"
            }), 409

        if new_employee_id != existing.get("employeeId"):
            existing_user = db.users.find_one({
                "username": new_employee_id.lower()
            })

            if existing_user:
                return jsonify({
                    "message": "Employee ID already exists"
                }), 409

            updates["employeeId"] = new_employee_id

    if not updates and not str(payload.get("password", "")).strip():
        return jsonify({
            "message": "No changes provided"
        }), 400

    try:
        if updates:
            updates["updatedAt"] = now_utc()

            db.employees.update_one(
                {"_id": object_id},
                {"$set": updates}
            )

        employee = db.employees.find_one({
            "_id": object_id
        })

        if not employee:
            return jsonify({
                "message": "Employee not found"
            }), 404

        old_employee_id = existing.get("employeeId")
        new_employee_id = employee.get("employeeId")

        user_updates = {
            "name": employee.get("name", ""),
            "department": employee.get("department", ""),
            "updatedAt": now_utc()
        }

        if new_employee_id != old_employee_id:
            user_updates["employeeId"] = new_employee_id
            user_updates["username"] = new_employee_id.lower()

        password = str(
            payload.get("password", "")
        ).strip()

        if password:
            if len(password) < 8:
                return jsonify({
                    "message": "Password must be at least 8 characters"
                }), 400

            user_updates["passwordHash"] = generate_password_hash(
                password
            )

        db.users.update_one(
            {"employeeId": old_employee_id},
            {"$set": user_updates}
        )

        updated_employee = db.employees.find_one({
            "_id": object_id
        })

        return jsonify({
            "message": "Employee updated successfully",
            "employee": serialize_employee(updated_employee)
        }), 200

    except Exception as error:
        print("UPDATE EMPLOYEE ERROR:", error)

        return jsonify({
            "message": "Unable to update employee"
        }), 500


@employees_bp.put("/<employee_id>/status")
@jwt_required()
def change_employee_status(employee_id):
    if not is_hr_admin():
        return jsonify({
            "message": "HR Admin permission required"
        }), 403

    try:
        object_id = ObjectId(employee_id)
    except Exception:
        return jsonify({
            "message": "Invalid employee id"
        }), 400

    payload = request.get_json(silent=True) or {}

    status = str(
        payload.get("status", "")
    ).strip()

    if status not in ["Active", "Inactive"]:
        return jsonify({
            "message": "Status must be Active or Inactive"
        }), 400

    employee = db.employees.find_one({
        "_id": object_id
    })

    if not employee:
        return jsonify({
            "message": "Employee not found"
        }), 404

    try:
        db.employees.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "status": status,
                    "updatedAt": now_utc()
                }
            }
        )

        db.users.update_one(
            {
                "employeeId": employee.get("employeeId")
            },
            {
                "$set": {
                    "status": status,
                    "updatedAt": now_utc()
                }
            }
        )

        updated_employee = db.employees.find_one({
            "_id": object_id
        })

        return jsonify({
            "message": f"Employee {status.lower()} successfully",
            "employee": serialize_employee(updated_employee)
        }), 200

    except Exception as error:
        print("STATUS UPDATE ERROR:", error)

        return jsonify({
            "message": "Unable to change employee status"
        }), 500


@employees_bp.put("/<employee_id>/credentials")
@jwt_required()
def set_employee_credentials(employee_id):
    if not is_hr_admin():
        return jsonify({
            "message": "HR Admin permission required"
        }), 403

    password = str(
        (request.get_json(silent=True) or {}).get(
            "password",
            ""
        )
    ).strip()

    if len(password) < 8:
        return jsonify({
            "message": "Password must be at least 8 characters"
        }), 400

    employee = db.employees.find_one({
        "employeeId": employee_id.strip().upper()
    })

    if not employee:
        return jsonify({
            "message": "Employee not found"
        }), 404

    employee_id = employee.get("employeeId")
    now = now_utc()

    user = db.users.find_one({
        "employeeId": employee_id
    })

    password_hash = generate_password_hash(password)

    if user:
        db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "passwordHash": password_hash,
                    "name": employee.get("name", ""),
                    "department": employee.get("department", ""),
                    "status": employee.get("status", "Active"),
                    "updatedAt": now
                }
            }
        )
    else:
        db.users.insert_one({
            "username": employee_id.lower(),
            "name": employee.get("name", ""),
            "passwordHash": password_hash,
            "role": "EMPLOYEE",
            "employeeId": employee_id,
            "department": employee.get("department", ""),
            "status": employee.get("status", "Active"),
            "createdAt": now,
            "updatedAt": now
        })

    return jsonify({
        "message": "Employee credentials saved"
    }), 200


@employees_bp.delete("/<employee_id>")
@jwt_required()
def delete_employee(employee_id):
    if not is_hr_admin():
        return jsonify({
            "message": "HR Admin permission required"
        }), 403

    try:
        object_id = ObjectId(employee_id)
    except Exception:
        return jsonify({
            "message": "Invalid employee id"
        }), 400

    employee = db.employees.find_one({
        "_id": object_id
    })

    if not employee:
        return jsonify({
            "message": "Employee not found"
        }), 404

    employee_code = employee.get("employeeId")

    try:
        db.employees.delete_one({
            "_id": object_id
        })

        db.users.delete_one({
            "employeeId": employee_code
        })

        return jsonify({
            "message": "Employee deleted successfully"
        }), 200

    except Exception as error:
        print("DELETE EMPLOYEE ERROR:", error)

        return jsonify({
            "message": "Unable to delete employee"
        }), 500