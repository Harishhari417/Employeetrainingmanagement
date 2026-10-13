from datetime import datetime, timezone
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from db import db

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


def parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def notice(items, kind, severity, title, message, action=None, training_id=None):
    item = {"type": kind, "severity": severity, "title": title, "message": message}
    if action:
        item["action"] = action
    if training_id:
        item["trainingId"] = str(training_id)
    items.append(item)


@notifications_bp.get("")
@jwt_required()
def notifications():
    claims = get_jwt()
    role = claims.get("role")
    employee_id = str(claims.get("employeeId") or "")
    department = claims.get("department")
    now = datetime.now(timezone.utc)
    items = []

    if role == "EMPLOYEE":
        # Training assigned to this employee as a trainee.
        participant_rows = list(db.training_participants.find({"employeeId": employee_id}))
        participant_by_training = {str(row.get("trainingId")): row for row in participant_rows if row.get("trainingId")}
        training_ids = list(participant_by_training.keys())
        from bson import ObjectId
        valid_ids = [ObjectId(value) for value in training_ids if ObjectId.is_valid(value)]
        assigned_trainings = list(db.trainings.find({"_id": {"$in": valid_ids}})) if valid_ids else []
        for training in assigned_trainings:
            tid = str(training.get("_id"))
            participant = participant_by_training.get(tid, {})
            title = training.get("title") or "Assigned training"
            end_date = parse_date(training.get("endDate") or training.get("startDate") or training.get("trainingDate"))
            start_date = parse_date(training.get("startDate") or training.get("trainingDate"))
            attendance = participant.get("attendance", "Pending")
            feedback_status = participant.get("feedbackStatus", "Pending")
            status = str(training.get("status", "")).lower()

            if attendance == "Pending" and end_date and end_date < now:
                notice(items, "attendance", "high", "Missed training — attendance pending", f"{title} has ended, but your attendance has not been marked. Contact the assigned trainer or manager.", "attendance", tid)
            elif attendance == "Pending" and start_date and start_date <= now and status not in {"completed", "cancelled"}:
                notice(items, "attendance", "medium", "Attendance not recorded", f"Attendance for {title} has not been recorded yet.", "attendance", tid)

            if attendance in {"Present", "Partial"} and feedback_status != "Submitted":
                notice(items, "feedback", "high", "Feedback submission required", f"Please submit your feedback for {title} so the training record can be completed.", "feedback", tid)

            if start_date and start_date > now and status not in {"completed", "cancelled"}:
                notice(items, "training", "low", "Upcoming assigned training", f"{title} is scheduled to start {start_date.strftime('%d %b %Y')}.", "training", tid)

        # This employee may also be a trainer and need to mark trainee attendance / review responses.
        owned_trainings = list(db.trainings.find({"trainerEmployeeId": employee_id, "status": {"$nin": ["Completed", "Cancelled"]}}))
        for training in owned_trainings:
            tid = str(training.get("_id"))
            title = training.get("title") or "Your training"
            end_date = parse_date(training.get("endDate") or training.get("startDate") or training.get("trainingDate"))
            if end_date and end_date <= now:
                pending_attendance = db.training_participants.count_documents({"trainingId": tid, "attendance": "Pending"})
                if pending_attendance:
                    notice(items, "attendance", "high", "Trainee attendance needs marking", f"{pending_attendance} trainee(s) still need attendance marked for {title}.", "attendance", tid)
            pending_feedback = db.training_participants.count_documents({"trainingId": tid, "attendance": {"$in": ["Present", "Partial"]}, "feedbackStatus": {"$ne": "Submitted"}})
            if pending_feedback:
                notice(items, "feedback", "medium", "Training feedback is outstanding", f"{pending_feedback} attendee(s) have not submitted feedback for {title}.", "feedback", tid)

        due = db.effectiveness_evaluations.count_documents({"employeeId": employee_id, "status": {"$in": ["Pending", "Overdue"]}})
        if due:
            notice(items, "evaluation", "medium", "Effectiveness evaluation due", f"You have {due} effectiveness evaluation(s) pending.", "evaluation")

    else:
        # HR sees portal-wide records. A manager is restricted to employees and trainings in their department.
        if role == "MANAGER":
            employee_ids = [row.get("employeeId") for row in db.employees.find({"department": department}, {"employeeId": 1, "_id": 0}) if row.get("employeeId")]
            participant_filter = {"employeeId": {"$in": employee_ids}}
            training_filter = {"$or": [{"departments": department}, {"trainerEmployeeId": employee_id}]}
            evaluation_filter = {"employeeId": {"$in": employee_ids}}
        else:
            participant_filter = {}
            training_filter = {}
            evaluation_filter = {}

        pending_attendance = list(db.training_participants.find({**participant_filter, "attendance": "Pending"}, {"trainingId": 1, "employeeId": 1, "_id": 0}).limit(1000))
        pending_feedback = list(db.training_participants.find({**participant_filter, "feedbackStatus": {"$ne": "Submitted"}, "attendance": {"$in": ["Present", "Partial"]}}, {"trainingId": 1, "employeeId": 1, "_id": 0}).limit(1000))
        attendance_by_training = {}
        feedback_by_training = {}
        for row in pending_attendance:
            attendance_by_training.setdefault(str(row.get("trainingId", "")), 0)
            attendance_by_training[str(row.get("trainingId", ""))] += 1
        for row in pending_feedback:
            feedback_by_training.setdefault(str(row.get("trainingId", "")), 0)
            feedback_by_training[str(row.get("trainingId", ""))] += 1

        from bson import ObjectId
        ids = set(attendance_by_training) | set(feedback_by_training)
        valid_ids = [ObjectId(value) for value in ids if ObjectId.is_valid(value)]
        query = {"_id": {"$in": valid_ids}}
        if role == "MANAGER":
            query["$or"] = [{"departments": department}, {"trainerEmployeeId": employee_id}]
        trainings = list(db.trainings.find(query)) if valid_ids else []
        titles = {str(row.get("_id")): row.get("title") or "Training" for row in trainings}
        for tid, count in attendance_by_training.items():
            if tid in titles:
                notice(items, "attendance", "high", "Attendance needs attention", f"{count} assigned trainee attendance record(s) are pending for {titles[tid]}.", "attendance", tid)
        for tid, count in feedback_by_training.items():
            if tid in titles:
                notice(items, "feedback", "medium", "Feedback responses pending", f"{count} attendee feedback response(s) are pending for {titles[tid]}.", "feedback", tid)

        due = db.effectiveness_evaluations.count_documents({**evaluation_filter, "status": {"$in": ["Pending", "Overdue"]}})
        if due:
            notice(items, "evaluation", "high", "Effectiveness reviews due", f"{due} effectiveness review(s) require attention.", "evaluation")

        # Highlight training completion blockers for HR and the department manager.
        for training in db.trainings.find(training_filter):
            tid = str(training.get("_id"))
            if str(training.get("status", "")).lower() in {"completed", "cancelled"}:
                continue
            participants = list(db.training_participants.find({"trainingId": tid}, {"attendance": 1, "feedbackStatus": 1, "_id": 0}))
            if not participants:
                continue
            missing_att = sum(1 for row in participants if row.get("attendance", "Pending") == "Pending")
            missing_feedback = sum(1 for row in participants if row.get("attendance") in {"Present", "Partial"} and row.get("feedbackStatus") != "Submitted")
            if missing_att == 0 and missing_feedback == 0:
                continue
            end_date = parse_date(training.get("endDate") or training.get("startDate") or training.get("trainingDate"))
            if end_date and end_date < now:
                detail = []
                if missing_att:
                    detail.append(f"{missing_att} attendance record(s) missing")
                if missing_feedback:
                    detail.append(f"{missing_feedback} feedback response(s) missing")
                notice(items, "training", "high", "Training completion blocked", f"{training.get('title', 'Training')}: " + "; ".join(detail) + ".", "training", tid)

    items.sort(key=lambda item: {"high": 0, "medium": 1, "low": 2}.get(item.get("severity"), 3))
    return jsonify({"count": len(items), "items": items, "updatedAt": now.isoformat()})
