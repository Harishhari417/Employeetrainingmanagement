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
        start_value=t.get("startDate",t.get("trainingDate"))
        end_value=t.get("endDate",start_value)
        status=t.get("status","Upcoming")
        from datetime import datetime, timezone
        try:
            start_dt=datetime.fromisoformat(str(start_value).replace("Z","+00:00")) if start_value else None
            if start_dt and start_dt.tzinfo is None: start_dt=start_dt.replace(tzinfo=timezone.utc)
            end_dt=datetime.fromisoformat(str(end_value).replace("Z","+00:00")) if end_value else start_dt
            if end_dt and end_dt.tzinfo is None: end_dt=end_dt.replace(tzinfo=timezone.utc)
            now=datetime.now(timezone.utc)
            if status not in {"Completed","Cancelled"}:
                status="Upcoming" if start_dt and now<start_dt else ("Ongoing" if end_dt and now<=end_dt else "Completed")
        except Exception:
            pass
        attendance_marked=sum(1 for p in ps if p.get("attendance") in {"Present","Absent","Partial"})
        scope="Company-wide" if not t.get("departments") and len(ps)>1 else ("Department" if t.get("departments") else ("One-to-one" if len(ps)==1 else "Custom / selected"))
        by_training.append({"id":tid,"name":t.get("title","Training"),"type":t.get("trainingType",""),"status":status,"scope":scope,"attendance":round(present/len(ps)*100,1) if ps else 0,"attendanceMarked":attendance_marked,"attendancePending":max(0,len(ps)-attendance_marked),"feedback":round(sum(vals)/len(vals),2) if vals else 0,"participants":len(ps),"feedbackResponses":len(fs),"startDate":start_value,"endDate":end_value,"period":str(start_value or "")[:7],"day":str(start_value or "")[:10]})
    types=sorted({x["type"] for x in by_training if x["type"]})
    by_type=[{"type":typ,"count":len([x for x in by_training if x["type"]==typ]),"attendance":round(sum(x["attendance"] for x in by_training if x["type"]==typ)/len([x for x in by_training if x["type"]==typ]),1) if any(x["type"]==typ for x in by_training) else 0,"feedback":round(sum(x["feedback"] for x in by_training if x["type"]==typ and x["feedback"]>0)/len([x for x in by_training if x["type"]==typ and x["feedback"]>0]),2) if any(x["type"]==typ and x["feedback"]>0 for x in by_training) else 0} for typ in types]
    from collections import Counter
    monthly=Counter(x["period"] for x in by_training if x.get("period"))
    daily=Counter(x["day"] for x in by_training if x.get("day"))
    status_counts={k:sum(1 for x in by_training if x.get("status")==k) for k in ("Upcoming","Ongoing","Completed","Cancelled")}
    return jsonify({"averageFeedback":round(sum(scores)/len(scores),2) if scores else 0,"attendancePercentage":round(sum(1 for p in participants if str(p.get("attendance","")).lower()=="present")/len(participants)*100,1) if participants else 0,"feedbackCount":len(feedback),"byTraining":by_training,"byType":by_type,"byMonth":[{"period":k,"scheduled":v,"completed":sum(1 for x in by_training if x["period"]==k and x["status"]=="Completed"),"ongoing":sum(1 for x in by_training if x["period"]==k and x["status"]=="Ongoing")} for k,v in sorted(monthly.items())],"byDay":[{"day":k,"scheduled":v,"completed":sum(1 for x in by_training if x["day"]==k and x["status"]=="Completed"),"ongoing":sum(1 for x in by_training if x["day"]==k and x["status"]=="Ongoing")} for k,v in sorted(daily.items())],"statusCounts":status_counts,"filters":{"trainingId":training_id,"startDate":start,"endDate":end}})
