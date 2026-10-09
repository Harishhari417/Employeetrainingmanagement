import csv, io
from flask import Blueprint, jsonify, Response, request
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
from db import db

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

def allowed_training(claims, training):
    if not training: return False
    if claims.get("role") == "HR_ADMIN": return True
    if claims.get("role") == "MANAGER":
        if claims.get("department") in training.get("departments", []):
            return True
        ids={x.get("employeeId") for x in db.employees.find({"department":claims.get("department")},{"employeeId":1,"_id":0})}
        return db.training_participants.count_documents({"trainingId":str(training["_id"]),"employeeId":{"$in":list(ids)}})>0
    return training.get("trainerEmployeeId") == claims.get("employeeId")

def training_or_404(training_id):
    if not ObjectId.is_valid(training_id): return None
    return db.trainings.find_one({"_id": ObjectId(training_id)})

def csv_response(rows, filename):
    out=io.StringIO()
    fields=list(rows[0].keys()) if rows else []
    if not fields: fields=["No data"]
    w=csv.DictWriter(out, fieldnames=fields); w.writeheader(); w.writerows(rows)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})

@reports_bp.get("/trainings")
@jwt_required()
def report_trainings():
    claims=get_jwt(); query={}
    if claims.get("role")=="MANAGER": query["departments"]=claims.get("department")
    rows=[{"_id":str(t["_id"]),"title":t.get("title",""),"startDate":t.get("startDate",t.get("trainingDate")),"endDate":t.get("endDate",t.get("startDate",t.get("trainingDate"))),"trainerName":t.get("trainerName",""),"status":t.get("status","Upcoming")} for t in db.trainings.find(query).sort("startDate",-1)]
    return jsonify(rows)

@reports_bp.get("/training/<training_id>/attendance")
@jwt_required()
def attendance_report(training_id):
    claims=get_jwt(); t=training_or_404(training_id)
    if not t or not allowed_training(claims,t): return jsonify({"message":"Training not found or access denied"}),403
    participants=list(db.training_participants.find({"trainingId":training_id}))
    rows=[]
    for p in participants:
        e=db.employees.find_one({"employeeId":p.get("employeeId")},{"name":1,"department":1,"_id":0}) or {}
        rows.append({"Employee ID":p.get("employeeId",""),"Employee":e.get("name",""),"Department":e.get("department",""),"Attendance":p.get("attendance","Pending"),"Marked By":p.get("attendanceMarkedBy",""),"Marked At":p.get("attendanceMarkedAt","")})
    if request.args.get("format")=="csv": return csv_response(rows,"attendance-report.csv")
    return jsonify({"training":{"id":training_id,"title":t.get("title","")},"rows":rows})

@reports_bp.get("/training/<training_id>/feedback")
@jwt_required()
def feedback_report(training_id):
    claims=get_jwt(); t=training_or_404(training_id)
    if not t or not allowed_training(claims,t): return jsonify({"message":"Training not found or access denied"}),403
    rows=[]
    for f in db.feedback.find({"trainingId":training_id}).sort("submittedAt",-1):
        e=db.employees.find_one({"employeeId":f.get("employeeId")},{"name":1,"department":1,"_id":0}) or {}
        rows.append({"Employee ID":f.get("employeeId",""),"Employee":e.get("name",""),"Department":e.get("department",""),"Overall":f.get("ratings",{}).get("overall",""),"Status":f.get("status","Pending"),"Submitted At":f.get("submittedAt","")})
    if request.args.get("format")=="csv": return csv_response(rows,"feedback-report.csv")
    return jsonify({"training":{"id":training_id,"title":t.get("title","")},"rows":rows})

@reports_bp.get("/training/<training_id>/trainee-trainer")
@jwt_required()
def trainee_trainer_report(training_id):
    claims=get_jwt(); t=training_or_404(training_id)
    if not t or not allowed_training(claims,t): return jsonify({"message":"Training not found or access denied"}),403
    trainer=t.get("trainerName","")
    rows=[]
    for p in db.training_participants.find({"trainingId":training_id}):
        e=db.employees.find_one({"employeeId":p.get("employeeId")},{"name":1,"department":1,"designation":1,"_id":0}) or {}
        rows.append({"Trainee ID":p.get("employeeId",""),"Trainee":e.get("name",""),"Department":e.get("department",""),"Designation":e.get("designation",""),"Trainer":trainer,"Trainer Employee ID":t.get("trainerEmployeeId",""),"Attendance":p.get("attendance","Pending"),"Feedback":p.get("feedbackStatus","Pending")})
    if request.args.get("format")=="csv": return csv_response(rows,"trainee-trainer-report.csv")
    return jsonify({"training":{"id":training_id,"title":t.get("title",""),"trainer":trainer},"rows":rows})
