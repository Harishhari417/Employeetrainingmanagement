from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from db import db

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

@bp.get("")
@jwt_required()
def analytics():
    feedback = list(db.feedback.find({}, {"ratings": 1}))
    scores = []
    for f in feedback:
        ratings = f.get("ratings", {})
        val = ratings.get("overall")
        if isinstance(val, (int, float)): scores.append(val)
        elif isinstance(val, str):
            mapping = {"Poor": 1, "Fair": 2, "Good": 3, "V Good": 4, "Excellent": 5}
            if val in mapping: scores.append(mapping[val])
    participants = list(db.training_participants.find({}, {"attendance": 1}))
    present = sum(1 for x in participants if x.get("attendance") == "Present")
    attendance = round(present / len(participants) * 100, 1) if participants else 0
    by_training = []
    for t in db.trainings.find().sort("trainingDate", 1).limit(20):
        tid = str(t["_id"]); ps = list(db.training_participants.find({"trainingId": tid}, {"attendance": 1}))
        p = sum(1 for x in ps if x.get("attendance") == "Present")
        fs = list(db.feedback.find({"trainingId": tid}, {"ratings": 1}))
        vals=[]
        for f in fs:
            v=f.get("ratings",{}).get("overall");
            if isinstance(v,(int,float)): vals.append(v)
            elif isinstance(v,str): vals.append({"Poor":1,"Fair":2,"Good":3,"V Good":4,"Excellent":5}.get(v,0))
        by_training.append({"name": t.get("title", "Training"), "attendance": round(p/len(ps)*100,1) if ps else 0, "feedback": round(sum(vals)/len(vals),2) if vals else 0})
    return jsonify({"averageFeedback": round(sum(scores)/len(scores),2) if scores else 0, "attendancePercentage": attendance, "feedbackCount": len(feedback), "byTraining": by_training})
