from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from db import db

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def score(value):
    if isinstance(value, (int, float)):
        return float(value)
    return {"Poor": 1, "Fair": 2, "Good": 3, "V Good": 4, "Excellent": 5}.get(value, 0)


@analytics_bp.get("")
@jwt_required()
def analytics():
    claims = get_jwt()
    role = claims.get("role")
    if role == "EMPLOYEE":
        employee_ids = [claims.get("employeeId")]
    elif role == "MANAGER":
        employee_ids = [x.get("employeeId") for x in db.employees.find({"department": claims.get("department")}, {"employeeId": 1, "_id": 0}) if x.get("employeeId")]
    else:
        employee_ids = None

    participant_query = {"employeeId": {"$in": employee_ids}} if employee_ids is not None else {}
    feedback_query = {"employeeId": {"$in": employee_ids}} if employee_ids is not None else {}
    feedback = list(db.feedback.find(feedback_query, {"ratings": 1, "trainingId": 1}))
    scores = [score(x.get("ratings", {}).get("overall")) for x in feedback]
    scores = [x for x in scores if x]
    participants = list(db.training_participants.find(participant_query, {"attendance": 1, "trainingId": 1}))
    present = sum(1 for x in participants if str(x.get("attendance", "")).lower() == "present")

    training_query = {}
    if employee_ids is not None:
        tids = db.training_participants.distinct("trainingId", participant_query)
        from bson import ObjectId
        training_query["_id"] = {"$in": [ObjectId(x) for x in tids if ObjectId.is_valid(x)]}

    by_training = []
    by_type = []
    for t in db.trainings.find(training_query).sort("trainingDate", 1):
        tid = str(t["_id"])
        ps = [p for p in participants if p.get("trainingId") == tid]
        present_count = sum(1 for p in ps if str(p.get("attendance", "")).lower() == "present")
        fs = [f for f in feedback if f.get("trainingId") == tid]
        vals = [score(f.get("ratings", {}).get("overall")) for f in fs]
        vals = [v for v in vals if v]
        by_training.append({"id": tid, "name": t.get("title", "Training"), "type": t.get("trainingType", ""), "attendance": round(present_count / len(ps) * 100, 1) if ps else 0, "feedback": round(sum(vals) / len(vals), 2) if vals else 0})

    for training_type in ["Technical", "Behavioural", "Leadership"]:
        matching = [x for x in by_training if x["type"] == training_type]
        by_type.append({"type": training_type, "count": len(matching), "attendance": round(sum(x["attendance"] for x in matching) / len(matching), 1) if matching else 0, "feedback": round(sum(x["feedback"] for x in matching if x["feedback"] > 0) / len([x for x in matching if x["feedback"] > 0]), 2) if any(x["feedback"] > 0 for x in matching) else 0})

    evaluations = list(db.effectiveness_evaluations.find({"employeeId": {"$in": employee_ids}} if employee_ids is not None else {}, {"requiredLevel": 1, "earlierLevel": 1, "presentLevel": 1, "status": 1}))
    completed_evaluations = sum(1 for x in evaluations if x.get("status") == "Completed")
    improvement = [x["presentLevel"] - x["earlierLevel"] for x in evaluations if isinstance(x.get("presentLevel"), (int, float)) and isinstance(x.get("earlierLevel"), (int, float))]

    return jsonify({
        "averageFeedback": round(sum(scores) / len(scores), 2) if scores else 0,
        "attendancePercentage": round(present / len(participants) * 100, 1) if participants else 0,
        "feedbackCount": len(feedback),
        "evaluationCount": len(evaluations),
        "completedEvaluations": completed_evaluations,
        "averageImprovement": round(sum(improvement) / len(improvement), 2) if improvement else 0,
        "byTraining": by_training,
        "byType": by_type,
    })
