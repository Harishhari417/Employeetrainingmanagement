from datetime import datetime, timezone

def serialize_employee(doc):
    if not doc:
        return None
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc

def build_employee(payload):
    now = datetime.now(timezone.utc)
    return {
        "employeeId": payload.get("employeeId", "").strip(),
        "name": payload.get("name", "").strip(),
        "department": payload.get("department", "").strip(),
        "designation": payload.get("designation", "").strip(),
        "reportingManager": payload.get("reportingManager", "").strip(),
        "email": payload.get("email", "").strip(),
        "status": payload.get("status", "Active"),
        "createdAt": now,
        "updatedAt": now,
    }
