from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

ROLES = {"HR_ADMIN", "MANAGER", "EMPLOYEE"}


def serialize_user(doc):
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "username": doc["username"],
        "name": doc["name"],
        "role": doc["role"],
        "employeeId": doc.get("employeeId"),
        "department": doc.get("department"),
        "email": doc.get("email"),
        "designation": doc.get("designation"),
    }


def build_user(username, name, password, role, employee_id=None, department=None):
    now = datetime.now(timezone.utc)
    return {
        "username": username.lower().strip(),
        "name": name.strip(),
        "passwordHash": generate_password_hash(password),
        "role": role,
        "employeeId": employee_id,
        "department": department,
        "email": "",
        "designation": "",
        "createdAt": now,
        "updatedAt": now,
    }
