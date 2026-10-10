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


@reports_bp.get("/training/<training_id>/excel")
@jwt_required()
def combined_training_excel(training_id):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    claims = get_jwt()
    training = training_or_404(training_id)
    if not training or not allowed_training(claims, training):
        return jsonify({"message": "Training not found or access denied"}), 403
    tid = training_id
    wb = Workbook()
    summary = wb.active
    summary.title = "Training Summary"
    summary.append(["Training", training.get("title", "")])
    summary.append(["Trainer", training.get("trainerName", "")])
    summary.append(["Trainer Employee ID", training.get("trainerEmployeeId", "")])
    summary.append(["Start Date", str(training.get("startDate", training.get("trainingDate", "")))])
    summary.append(["End Date", str(training.get("endDate", ""))])
    summary.append(["Status", training.get("status", "Upcoming")])
    attendance = wb.create_sheet("Attendance")
    attendance.append(["Employee ID", "Employee", "Department", "Attendance", "Marked By", "Marked At"])
    feedback_sheet = wb.create_sheet("Feedback")
    feedback_sheet.append(["Employee ID", "Employee", "Department", "Overall Rating", "Status", "Submitted At", "Trainer", "Trainer Employee ID"])
    trainee_trainer = wb.create_sheet("Trainee-Trainer")
    trainee_trainer.append(["Trainee ID", "Trainee", "Department", "Designation", "Trainer", "Trainer Employee ID", "Attendance", "Feedback"])
    for part in db.training_participants.find({"trainingId": tid}):
        e = db.employees.find_one({"employeeId": part.get("employeeId")}, {"name": 1, "department": 1, "designation": 1, "_id": 0}) or {}
        attendance.append([part.get("employeeId", ""), e.get("name", ""), e.get("department", ""), part.get("attendance", "Pending"), str(part.get("attendanceMarkedBy", "")), str(part.get("attendanceMarkedAt", ""))])
        trainee_trainer.append([part.get("employeeId", ""), e.get("name", ""), e.get("department", ""), e.get("designation", ""), training.get("trainerName", ""), training.get("trainerEmployeeId", ""), part.get("attendance", "Pending"), part.get("feedbackStatus", "Pending")])
    for f in db.feedback.find({"trainingId": tid}).sort("submittedAt", -1):
        e = db.employees.find_one({"employeeId": f.get("employeeId")}, {"name": 1, "department": 1, "_id": 0}) or {}
        feedback_sheet.append([f.get("employeeId", ""), e.get("name", ""), e.get("department", ""), f.get("ratings", {}).get("overall", ""), f.get("status", "Pending"), str(f.get("submittedAt", "")), training.get("trainerName", ""), training.get("trainerEmployeeId", "")])
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="4338CA")
            cell.alignment = Alignment(wrap_text=True)
        for col in ws.columns:
            letter = get_column_letter(col[0].column)
            ws.column_dimensions[letter].width = min(34, max(14, max(len(str(c.value or "")) for c in col) + 2))
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(output.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=training-{training_id}-report.xlsx"})


@reports_bp.get("/monthly/excel")
@jwt_required()
def monthly_training_excel():
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    claims = get_jwt()
    year = request.args.get("year", str(__import__("datetime").datetime.now().year))
    month = request.args.get("month", "")
    query = {}
    if claims.get("role") == "MANAGER":
        query["departments"] = claims.get("department")
    rows = []
    for t in db.trainings.find(query).sort("startDate", 1):
        raw = str(t.get("startDate", t.get("trainingDate", "")))[:10]
        if len(raw) < 7 or raw[:4] != year or (month and raw[5:7] != month.zfill(2)):
            continue
        tid = str(t["_id"])
        participants = list(db.training_participants.find({"trainingId": tid}))
        feedbacks = list(db.feedback.find({"trainingId": tid, "status": "Submitted"}))
        present = sum(1 for p in participants if p.get("attendance") == "Present")
        rows.append([raw[:7], t.get("title", ""), t.get("trainingType", ""), t.get("trainerName", ""), raw, str(t.get("endDate", ""))[:10], t.get("status", "Upcoming"), len(participants), present, round(present / len(participants) * 100, 1) if participants else 0, len(feedbacks), round(sum(float(f.get("ratings", {}).get("overall", 0) or 0) for f in feedbacks) / len(feedbacks), 2) if feedbacks else 0, "Company-wide" if not t.get("departments") else ", ".join(t.get("departments", [])), "One-to-one" if len(participants) == 1 else "Custom / Group" if t.get("traineeIds") else "Unassigned"])
    wb = Workbook()
    ws = wb.active
    ws.title = "Monthly Overview"
    ws.append(["Month", "Training", "Type", "Trainer", "Start", "End", "Status", "Assigned", "Present", "Attendance %", "Feedback Responses", "Average Feedback / 5", "Scope", "Assignment Type"])
    for row in rows: ws.append(row)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="4338CA")
    ws.freeze_panes = "A2"
    for col in ws.columns:
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(32, max(14, max(len(str(c.value or "")) for c in col) + 2))
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(output.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=training-monthly-report-{year}{('-'+month.zfill(2)) if month else ''}.xlsx"})
