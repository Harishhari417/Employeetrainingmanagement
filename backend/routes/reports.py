import csv, io
from flask import Blueprint, jsonify, Response, request
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
from db import db
from datetime import datetime
from openpyxl import Workbook

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


def workbook_response(sheets, filename):
    book = Workbook()
    book.remove(book.active)
    for title, rows in sheets:
        ws = book.create_sheet(title[:31])
        fields = list(rows[0].keys()) if rows else ["No data"]
        ws.append(fields)
        for row in rows:
            ws.append([str(row.get(field, "") if row.get(field) is not None else "") for field in fields])
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for column in ws.columns:
            letter = column[0].column_letter
            width = min(42, max(12, max((len(str(cell.value or "")) for cell in column), default=10) + 2))
            ws.column_dimensions[letter].width = width
    output = io.BytesIO()
    book.save(output)
    output.seek(0)
    return Response(output.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={filename}"})


def build_training_sheets(training):
    training_id = str(training["_id"])
    attendance_rows = []
    feedback_rows = []
    relation_rows = []
    participants = list(db.training_participants.find({"trainingId": training_id}))
    for participant in participants:
        employee = db.employees.find_one({"employeeId": participant.get("employeeId")}, {"_id": 0, "name": 1, "department": 1}) or {}
        common = {"Training": training.get("title", ""), "Training Type": training.get("trainingType", ""), "Trainer": training.get("trainerName", ""), "Trainer ID": training.get("trainerEmployeeId", ""), "Employee ID": participant.get("employeeId", ""), "Employee": employee.get("name", ""), "Department": employee.get("department", "")}
        attendance_rows.append({**common, "Attendance": participant.get("attendance", "Pending"), "Attendance Updated": participant.get("attendanceUpdatedAt", "")})
        relation_rows.append({**common, "Start Date": training.get("startDate", training.get("trainingDate", "")), "End Date": training.get("endDate", ""), "Assignment Scope": "Company-wide" if len(participants) > 1 and not training.get("departments") else ("Department" if training.get("departments") else ("One-to-one" if len(participants) == 1 else "Custom / selected")), "Completion": participant.get("completionStatus", "Not Started"), "Feedback Status": participant.get("feedbackStatus", "Pending")})
        feedback = db.feedback.find_one({"trainingId": training_id, "employeeId": participant.get("employeeId")}, {"_id": 0}) or {}
        if feedback:
            ratings = feedback.get("ratings", {}) or {}
            feedback_rows.append({**common, "Overall Rating": ratings.get("overall", ""), "Programme Design": ratings.get("Programme Design", ""), "Presentation": ratings.get("Presentation of Information", ""), "Information Amount": ratings.get("Amount of Information", ""), "Submitted At": feedback.get("submittedAt", ""), "Remarks": feedback.get("remarks", "")})
    summary = [{"Training": training.get("title", ""), "Type": training.get("trainingType", ""), "Trainer": training.get("trainerName", ""), "Trainer ID": training.get("trainerEmployeeId", ""), "Start Date": training.get("startDate", training.get("trainingDate", "")), "End Date": training.get("endDate", ""), "Status": training.get("status", "Upcoming"), "Participants": len(participants), "Attendance Marked": sum(1 for x in participants if x.get("attendance") in {"Present", "Absent", "Partial"}), "Present": sum(1 for x in participants if x.get("attendance") == "Present"), "Feedback Responses": len(feedback_rows), "Assignment Scope": "Company-wide" if len(participants) > 1 and not training.get("departments") else ("Department" if training.get("departments") else ("One-to-one" if len(participants) == 1 else "Custom / selected"))}]
    return [("Training Summary", summary), ("Attendance", attendance_rows), ("Feedback", feedback_rows), ("Trainee-Trainer", relation_rows)]


@reports_bp.get("/training/<training_id>/excel")
@jwt_required()
def training_excel_report(training_id):
    claims = get_jwt()
    training = training_or_404(training_id)
    if not training or not allowed_training(claims, training):
        return jsonify({"message": "Training not found or access denied"}), 403
    safe = "".join(ch for ch in training.get("title", "training") if ch.isalnum() or ch in "-_")[:45] or "training"
    return workbook_response(build_training_sheets(training), f"{safe}-report.xlsx")


@reports_bp.get("/monthly/excel")
@jwt_required()
def monthly_excel_report():
    claims = get_jwt()
    year = request.args.get("year", str(datetime.now().year))
    month = request.args.get("month", str(datetime.now().month))
    try:
        year, month = int(year), int(month)
        if month < 1 or month > 12: raise ValueError()
    except ValueError:
        return jsonify({"message": "A valid year and month are required"}), 400
    prefix = f"{year:04d}-{month:02d}"
    query = {"startDate": {"$regex": "^" + prefix}}
    trainings = list(db.trainings.find(query).sort("startDate", 1))
    if claims.get("role") == "MANAGER":
        trainings = [t for t in trainings if claims.get("department") in t.get("departments", []) or db.training_participants.count_documents({"trainingId": str(t["_id"]), "employeeId": {"$in": [x.get("employeeId") for x in db.employees.find({"department": claims.get("department")}, {"employeeId": 1, "_id": 0})]}}) > 0]
    elif claims.get("role") == "EMPLOYEE":
        trainings = [t for t in trainings if t.get("trainerEmployeeId") == claims.get("employeeId") or db.training_participants.count_documents({"trainingId": str(t["_id"]), "employeeId": claims.get("employeeId")}) > 0]
    sheets = [("Monthly Summary", [{"Month": prefix, "Trainings Scheduled": len(trainings), "Completed": sum(1 for t in trainings if t.get("status") == "Completed"), "Cancelled": sum(1 for t in trainings if t.get("status") == "Cancelled"), "Ongoing / Upcoming": sum(1 for t in trainings if t.get("status") not in {"Completed", "Cancelled"})}])]
    summary_rows = []
    for t in trainings:
        p_rows = list(db.training_participants.find({"trainingId": str(t["_id"])}))
        feedback_rows = list(db.feedback.find({"trainingId": str(t["_id"])}, {"ratings": 1, "_id": 0}))
        ratings = [float(f.get("ratings", {}).get("overall")) for f in feedback_rows if isinstance(f.get("ratings", {}).get("overall"), (int, float))]
        summary_rows.append({"Training": t.get("title", ""), "Type": t.get("trainingType", ""), "Trainer": t.get("trainerName", ""), "Trainer ID": t.get("trainerEmployeeId", ""), "Start Date": t.get("startDate", t.get("trainingDate", "")), "End Date": t.get("endDate", ""), "Status": t.get("status", "Upcoming"), "Scope": "Company-wide" if len(p_rows) > 1 and not t.get("departments") else ("Department" if t.get("departments") else ("One-to-one" if len(p_rows) == 1 else "Custom / selected")), "Participants": len(p_rows), "Present": sum(1 for x in p_rows if x.get("attendance") == "Present"), "Attendance Marked": sum(1 for x in p_rows if x.get("attendance") in {"Present", "Absent", "Partial"}), "Feedback Responses": len(feedback_rows), "Average Feedback": round(sum(ratings) / len(ratings), 2) if ratings else ""})
        if allowed_training(claims, t):
            sheets.extend(build_training_sheets(t)[1:])
    sheets.insert(1, ("Training Details", summary_rows))
    return workbook_response(sheets, f"training-report-{prefix}.xlsx")
