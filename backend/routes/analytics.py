from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
from db import db

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

def score(value):
    if isinstance(value, (int, float)): return float(value)
    return {"Poor": 1, "Fair": 2, "Good": 3, "V Good": 4, "Excellent": 5}.get(value, 0)

def date_text(value):
    if hasattr(value, "isoformat"): return value.isoformat()
    return str(value or "")

def current_status(training):
    stored = training.get("status", "Upcoming")
    if stored in {"Completed", "Cancelled"}: return stored
    try:
        start = datetime.fromisoformat(date_text(training.get("startDate", training.get("trainingDate"))).replace("Z", "+00:00"))
        end = datetime.fromisoformat(date_text(training.get("endDate", training.get("startDate", training.get("trainingDate")))).replace("Z", "+00:00"))
        now = datetime.now(start.tzinfo or timezone.utc)
        if now < start: return "Upcoming"
        if now <= end: return "Ongoing"
        return "Ongoing"  # Past sessions remain open until attendance and feedback are submitted.
    except Exception: return "Upcoming"

@analytics_bp.get("")
@jwt_required()
def analytics():
    claims = get_jwt(); role = claims.get("role")
    training_id = request.args.get("trainingId", "").strip(); start = request.args.get("startDate", "").strip(); end = request.args.get("endDate", "").strip()
    period = request.args.get("period", "month").lower()
    if period not in {"day", "week", "month", "year"}: period = "month"
    employee_ids = None
    if role == "EMPLOYEE": employee_ids = [claims.get("employeeId")]
    elif role == "MANAGER": employee_ids = [x.get("employeeId") for x in db.employees.find({"department": claims.get("department")}, {"employeeId": 1, "_id": 0}) if x.get("employeeId")]
    training_query = {}
    if role == "EMPLOYEE":
        assigned = db.training_participants.distinct("trainingId", {"employeeId": claims.get("employeeId")})
        own = [str(x["_id"]) for x in db.trainings.find({"trainerEmployeeId": claims.get("employeeId")}, {"_id": 1})]
        training_query["_id"] = {"$in": [ObjectId(x) for x in set(assigned + own) if ObjectId.is_valid(x)]}
    elif role == "MANAGER":
        assigned = db.training_participants.distinct("trainingId", {"employeeId": {"$in": employee_ids or []}})
        training_query["_id"] = {"$in": [ObjectId(x) for x in assigned if ObjectId.is_valid(x)]}
    if training_id and ObjectId.is_valid(training_id): training_query["_id"] = ObjectId(training_id)
    date_range = {}
    if start: date_range["$gte"] = start
    if end: date_range["$lte"] = end + "T23:59:59"
    if date_range: training_query["startDate"] = date_range
    trainings = list(db.trainings.find(training_query).sort("startDate", 1))
    tids = [str(t["_id"]) for t in trainings]
    participant_query = {"trainingId": {"$in": tids}}
    if employee_ids is not None and role != "EMPLOYEE": participant_query["employeeId"] = {"$in": employee_ids}
    participants = list(db.training_participants.find(participant_query, {"attendance": 1, "feedbackStatus": 1, "trainingId": 1, "employeeId": 1}))
    feedback_query = {"trainingId": {"$in": tids}}
    if role == "EMPLOYEE":
        trainer_ids = [tid for tid in tids if db.trainings.find_one({"_id": ObjectId(tid), "trainerEmployeeId": claims.get("employeeId")}, {"_id": 1})]
        feedback_query["$or"] = [{"employeeId": claims.get("employeeId")}, {"trainingId": {"$in": trainer_ids}}]
    elif employee_ids is not None: feedback_query["employeeId"] = {"$in": employee_ids}
    feedback = list(db.feedback.find(feedback_query, {"ratings": 1, "trainingId": 1, "employeeId": 1}))
    scores = [score(x.get("ratings", {}).get("overall")) for x in feedback]; scores = [x for x in scores if x]
    by_training = []; buckets = {}; by_type = {}
    for t in trainings:
        tid = str(t["_id"]); ps = [p for p in participants if p.get("trainingId") == tid]; fs = [f for f in feedback if f.get("trainingId") == tid]
        vals = [score(f.get("ratings", {}).get("overall")) for f in fs]; vals = [v for v in vals if v]
        present = sum(1 for p in ps if p.get("attendance") in {"Present", "Partial"})
        attendance_marked = sum(1 for p in ps if p.get("attendance") not in {None, "", "Pending"})
        status = current_status(t); raw = date_text(t.get("startDate", t.get("trainingDate"))); day = raw[:10]
        try: dt = datetime.fromisoformat(raw.replace("Z", "+00:00")); month_key = dt.strftime("%Y-%m"); year_key = dt.strftime("%Y"); week_key = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"
        except Exception: month_key = day[:7] if len(day) >= 7 else "Unknown"; year_key = day[:4] if len(day) >= 4 else "Unknown"; week_key = "Unknown"
        total = len(ps); scope = "One-to-one / Custom" if total <= 1 else "Company-wide / Department"
        item = {"id": tid, "name": t.get("title", "Training"), "type": t.get("trainingType", "Other"), "attendance": round(present / total * 100, 1) if total else 0, "attendanceMarked": attendance_marked, "feedback": round(sum(vals) / len(vals), 2) if vals else 0, "participants": total, "feedbackResponses": len(fs), "feedbackCompletion": round(len(fs) / total * 100, 1) if total else 0, "startDate": raw, "status": status, "scope": scope, "trainer": t.get("trainerName", "")}
        by_training.append(item)
        for key, label in [(day, day), (week_key, week_key), (month_key, month_key), (year_key, year_key)]:
            if key not in buckets: buckets[key] = {"period": label, "scheduled": 0, "completed": 0, "ongoing": 0, "upcoming": 0, "cancelled": 0, "attendance": [], "feedback": [], "oneToOne": 0, "companyWide": 0}
            b = buckets[key]; b["scheduled"] += 1; b[status.lower()] = b.get(status.lower(), 0) + 1
            b["attendance"].append(item["attendance"]); b["feedback"].append(item["feedback"])
            b["oneToOne" if total <= 1 else "companyWide"] += 1
        typ = item["type"] or "Other"
        by_type.setdefault(typ, {"type": typ, "count": 0, "attendanceValues": [], "feedbackValues": []})
        by_type[typ]["count"] += 1; by_type[typ]["attendanceValues"].append(item["attendance"])
        if item["feedback"]: by_type[typ]["feedbackValues"].append(item["feedback"])
    by_period = []
    for key, b in sorted(buckets.items()):
        if period == "day" and len(key) != 10: continue
        if period == "week" and "-W" not in key: continue
        if period == "month" and len(key) != 7: continue
        if period == "year" and len(key) != 4: continue
        by_period.append({"period": b["period"], "scheduled": b["scheduled"], "completed": b["completed"], "ongoing": b["ongoing"], "upcoming": b["upcoming"], "cancelled": b["cancelled"], "attendance": round(sum(b["attendance"])/len(b["attendance"]),1) if b["attendance"] else 0, "feedback": round(sum(b["feedback"])/len(b["feedback"]),2) if b["feedback"] else 0, "oneToOne": b["oneToOne"], "companyWide": b["companyWide"]})
    type_rows = [{"type": v["type"], "count": v["count"], "attendance": round(sum(v["attendanceValues"])/len(v["attendanceValues"]),1) if v["attendanceValues"] else 0, "feedback": round(sum(v["feedbackValues"])/len(v["feedbackValues"]),2) if v["feedbackValues"] else 0} for v in by_type.values()]
    total_present = sum(1 for p in participants if p.get("attendance") in {"Present", "Partial"})
    return jsonify({"averageFeedback": round(sum(scores)/len(scores),2) if scores else 0, "attendancePercentage": round(total_present/len(participants)*100,1) if participants else 0, "attendanceMarked": sum(1 for p in participants if p.get("attendance") not in {None,"","Pending"}), "participantCount": len(participants), "feedbackCount": len(feedback), "byTraining": by_training, "byType": type_rows, "byPeriod": by_period, "period": period, "filters": {"trainingId": training_id, "startDate": start, "endDate": end}})
