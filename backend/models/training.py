from datetime import datetime, timezone

def serialize_training(doc):
    if not doc:
        return None
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc

def build_training(payload):
    now = datetime.now(timezone.utc)
    start = payload.get("startDate") or payload.get("trainingDate")
    end = payload.get("endDate") or start
    return {
        "title": str(payload.get("title", "")).strip(),
        "content": str(payload.get("content", "")).strip(),
        "trainingType": str(payload.get("trainingType", "")).strip(),
        "trainerName": str(payload.get("trainerName", "")).strip(),
        "trainerEmployeeId": str(payload.get("trainerEmployeeId", "")).strip(),
        "trainerCategory": payload.get("trainerCategory", "Internal"),
        "venue": str(payload.get("venue", "")).strip(),
        "departments": payload.get("departments", []),
        "traineeIds": payload.get("traineeIds", []),
        "startDate": start,
        "endDate": end,
        "trainingDate": start,
        "trainingMode": payload.get("trainingMode", "Offline"),
        "status": payload.get("status", "Upcoming"),
        "createdAt": now,
        "updatedAt": now,
    }
