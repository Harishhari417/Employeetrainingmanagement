from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from db import db

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

@notifications_bp.get("")
@jwt_required()
def notifications():
    claims=get_jwt(); role=claims.get("role"); employee_id=claims.get("employeeId"); department=claims.get("department"); items=[]
    now=datetime.now(timezone.utc)
    if role=="EMPLOYEE":
        # If this employee is the assigned trainer, show missing trainee attendance.
        trainer_trainings=list(db.trainings.find({"trainerEmployeeId":employee_id,"status":{"$nin":["Completed","Cancelled"]}},{"_id":1,"title":1,"endDate":1,"startDate":1}))
        missing_att=0
        for t in trainer_trainings:
            end=t.get("endDate") or t.get("startDate")
            try: due=datetime.fromisoformat(str(end).replace("Z","+00:00")) if end else now
            except Exception: due=now
            if due.tzinfo is None: due=due.replace(tzinfo=timezone.utc)
            if due <= now:
                missing_att += db.training_participants.count_documents({"trainingId":str(t["_id"]),"attendance":"Pending"})
        if missing_att:
            items.append({"type":"attendance","severity":"high","title":"Attendance pending","message":f"{missing_att} trainee attendance record(s) are still missing."})
        assigned_pending=db.training_participants.count_documents({"employeeId":employee_id,"feedbackStatus":"Pending","attendance":{"$in":["Present","Partial"]}})
        if assigned_pending:
            items.append({"type":"feedback","severity":"high","title":"Feedback pending","message":f"{assigned_pending} completed/attended training feedback response(s) need your attention."})
        due=db.effectiveness_evaluations.count_documents({"employeeId":employee_id,"status":{"$in":["Pending","Overdue"]}})
        if due: items.append({"type":"evaluation","severity":"medium","title":"Evaluation due","message":f"{due} effectiveness evaluation(s) are pending."})
    else:
        base={}
        if role=="MANAGER":
            ids=[x.get("employeeId") for x in db.employees.find({"department":department},{"employeeId":1,"_id":0})]
            base={"employeeId":{"$in":ids}}
        pending_att=db.training_participants.count_documents({**base,"attendance":"Pending"})
        if pending_att: items.append({"type":"attendance","severity":"high","title":"Attendance missing","message":f"{pending_att} assigned trainee attendance record(s) are missing."})
        pending_feedback=db.training_participants.count_documents({**base,"feedbackStatus":"Pending","attendance":{"$in":["Present","Partial"]}})
        if pending_feedback: items.append({"type":"feedback","severity":"medium","title":"Feedback pending","message":f"{pending_feedback} participant feedback response(s) are still pending."})
        pending_eval=db.effectiveness_evaluations.count_documents({**base,"status":{"$in":["Pending","Overdue"]}})
        if pending_eval: items.append({"type":"evaluation","severity":"high","title":"Effectiveness reviews due","message":f"{pending_eval} evaluation(s) require attention."})
    return jsonify({"count":len(items),"items":items})
