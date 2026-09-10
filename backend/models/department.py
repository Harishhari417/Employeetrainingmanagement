from datetime import datetime, timezone

def serialize_department(doc):
    if not doc:
        return None
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc

def build_department(payload):
    now = datetime.now(timezone.utc)
    return {
        "name": payload.get("name", "").strip(),
        "status": payload.get("status", "Active"),
        "createdAt": now,
        "updatedAt": now,
    }
