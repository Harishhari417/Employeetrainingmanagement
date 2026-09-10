from datetime import datetime, timezone
from bson import ObjectId

def serialize_training(doc):
    if not doc:
        return None
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc

def build_training(payload):
    now = datetime.now(timezone.utc)
    return {
        "title": payload.get("title", "").strip(),
        "content": payload.get("content", "").strip(),
        "trainingType": payload.get("trainingType", "Technical"),
        "trainerName": payload.get("trainerName", "").strip(),
        "trainerCategory": payload.get("trainerCategory", "Internal"),
        "venue": payload.get("venue", "").strip(),
        "departments": payload.get("departments", []),
        "traineeIds": payload.get("traineeIds", []),
        "trainingDate": payload.get("trainingDate"),
        "trainingMode": payload.get("trainingMode", "Company-wide"),
        "durationMinutes": int(payload.get("durationMinutes", 0) or 0),
        "status": payload.get("status", "Scheduled"),
        "createdAt": now,
        "updatedAt": now,
    }
