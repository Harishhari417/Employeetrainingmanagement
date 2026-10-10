from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
from db import db

analytics_bp=Blueprint("analytics",__name__,url_prefix="/api/analytics")
def score(value):
    if isinstance(value,(int,float)): return float(value)
    return {"Poor":1,"Fair":2,"Good":3,"V Good":4,"Excellent":5}.get(value,0)

@analytics_bp.get("")
@jwt_required()
def analytics():
    claims=get_jwt(); role=claims.get("role"); training_id=request.args.get("trainingId","").strip(); start=request.args.get("startDate","").strip(); end=request.args.get("endDate","").strip()
    if role=="EMPLOYEE": employee_ids=[claims.get("employeeId")]
    elif role=="MANAGER": employee_ids=[x.get("employeeId") for x in db.employees.find({"department":claims.get("department")},{"employeeId":1,"_id":0}) if x.get("employeeId")]
    else: employee_ids=None
    participant_query={"employeeId":{"$in":employee_ids}} if employee_ids is not None else {}
    tids=db.training_participants.distinct("trainingId",participant_query)
    training_query={}
    if employee_ids is not None: training_query["_id"]={"$in":[ObjectId(x) for x in tids if ObjectId.is_valid(x)]}
    if training_id and ObjectId.is_valid(training_id): training_query["_id"]=ObjectId(training_id)
    date_query={}
    if start: date_query["$gte"]=start
    if end: date_query["$lte"]=end+"T23:59:59"
    if date_query: training_query["startDate"]=date_query
    trainings=list(db.trainings.find(training_query).sort("startDate",1))
    valid_tids={str(t["_id"]) for t in trainings}
    participant_query["trainingId"]={"$in":list(valid_tids)}
    participants=list(db.training_participants.find(participant_query,{"attendance":1,"trainingId":1,"employeeId":1}))
    feedback_query={"trainingId":{"$in":list(valid_tids)}}
    if employee_ids is not None: feedback_query["employeeId"]={"$in":employee_ids}
    feedback=list(db.feedback.find(feedback_query,{"ratings":1,"trainingId":1,"employeeId":1}))
    scores=[score(x.get("ratings",{}).get("overall")) for x in feedback];scores=[x for x in scores if x]
    by_training=[]
    for t in trainings:
        tid=str(t["_id"]);ps=[p for p in participants if p.get("trainingId")==tid];fs=[f for f in feedback if f.get("trainingId")==tid];vals=[score(f.get("ratings",{}).get("overall")) for f in fs];vals=[v for v in vals if v];present=sum(1 for p in ps if str(p.get("attendance","")).lower()=="present")
        by_training.append({"id":tid,"name":t.get("title","Training"),"type":t.get("trainingType",""),"attendance":round(present/len(ps)*100,1) if ps else 0,"feedback":round(sum(vals)/len(vals),2) if vals else 0,"participants":len(ps),"feedbackResponses":len(fs),"startDate":t.get("startDate",t.get("trainingDate"))})
    for item, training in zip(by_training, trainings):
        participants_for_training = [p for p in participants if p.get("trainingId") == item["id"]]
        item["status"] = training.get("status", "Upcoming")
        item["assignmentType"] = "One-to-one" if len(participants_for_training) == 1 else ("Custom / Group" if participants_for_training else "Unassigned")
        item["scope"] = "Company-wide" if not training.get("departments") else ", ".join(training.get("departments", []))
    period_map = {}
    for t in trainings:
        raw = str(t.get("startDate", t.get("trainingDate", "")))
        period = raw[:10] if len(raw) >= 10 else "Unscheduled"
        item = period_map.setdefault(period, {"period": period, "scheduled": 0, "completed": 0, "ongoing": 0, "upcoming": 0, "feedbackResponses": 0, "attendanceMarked": 0, "participants": 0})
        item["scheduled"] += 1
        status_value = t.get("status", "Upcoming")
        if status_value == "Completed": item["completed"] += 1
        elif status_value == "Cancelled": pass
        elif status_value == "Ongoing": item["ongoing"] += 1
        else: item["upcoming"] += 1
        ps = [p for p in participants if p.get("trainingId") == str(t["_id"])]
        fs = [f for f in feedback if f.get("trainingId") == str(t["_id"])]
        item["feedbackResponses"] += len(fs)
        item["attendanceMarked"] += sum(1 for p in ps if p.get("attendance") in {"Present", "Absent", "Partial"})
        item["participants"] += len(ps)
    by_period = [period_map[k] for k in sorted(period_map)]
    types=sorted({x["type"] for x in by_training if x["type"]})
    by_type=[{"type":typ,"count":len([x for x in by_training if x["type"]==typ]),"attendance":round(sum(x["attendance"] for x in by_training if x["type"]==typ)/len([x for x in by_training if x["type"]==typ]),1) if any(x["type"]==typ for x in by_training) else 0,"feedback":round(sum(x["feedback"] for x in by_training if x["type"]==typ and x["feedback"]>0)/len([x for x in by_training if x["type"]==typ and x["feedback"]>0]),2) if any(x["type"]==typ and x["feedback"]>0 for x in by_training) else 0} for typ in types]
    return jsonify({"averageFeedback":round(sum(scores)/len(scores),2) if scores else 0,"attendancePercentage":round(sum(1 for p in participants if str(p.get("attendance","")).lower()=="present")/len(participants)*100,1) if participants else 0,"feedbackCount":len(feedback),"byTraining":by_training,"byType":by_type,"byPeriod":by_period,"filters":{"trainingId":training_id,"startDate":start,"endDate":end}})
