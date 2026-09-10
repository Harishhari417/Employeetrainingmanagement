import csv
import io
from flask import Blueprint, Response, request
from flask_jwt_extended import jwt_required, get_jwt
from db import db

bp = Blueprint("reports", __name__, url_prefix="/api/reports")

@bp.get("/training")
@jwt_required()
def training_report():
    claims = get_jwt()
    if claims.get("role") not in {"HR_ADMIN", "MANAGER"}:
        return {"message": "Manager or HR Admin permission required"}, 403

    department = request.args.get("department")
    query = {}
    if claims.get("role") == "MANAGER":
        query["departments"] = claims.get("department")
    elif department:
        query["departments"] = department

    rows = []
    for training in db.trainings.find(query).sort("trainingDate", 1):
        tid = str(training["_id"])
        participants = list(db.training_participants.find({"trainingId": tid}))
        present = sum(1 for p in participants if p.get("attendance") == "Present")
        feedback = list(db.feedback.find({"trainingId": tid}))
        rows.append({
            "Training": training.get("title", ""),
            "Type": training.get("trainingType", ""),
            "Trainer": training.get("trainerName", ""),
            "Date": training.get("trainingDate", ""),
            "Venue": training.get("venue", ""),
            "Status": training.get("status", ""),
            "Participants": len(participants),
            "Present": present,
            "Attendance %": round(present / len(participants) * 100, 1) if participants else 0,
            "Feedback Responses": len(feedback),
        })

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()) if rows else ["Training","Type","Trainer","Date","Venue","Status","Participants","Present","Attendance %","Feedback Responses"])
    writer.writeheader()
    writer.writerows(rows)
    return Response(out.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition": "attachment; filename=training-report.csv"
    })

@bp.get("/employees")
@jwt_required()
def employee_report():
    if get_jwt().get("role") != "HR_ADMIN":
        return {"message": "HR Admin permission required"}, 403

    rows = []
    for employee in db.employees.find().sort("name", 1):
        employee_id = employee.get("employeeId")
        participants = list(db.training_participants.find({"employeeId": employee_id}))
        present = sum(1 for p in participants if p.get("attendance") == "Present")
        rows.append({
            "Employee ID": employee_id,
            "Name": employee.get("name", ""),
            "Department": employee.get("department", ""),
            "Designation": employee.get("designation", ""),
            "Reporting Manager": employee.get("reportingManager", ""),
            "Training Assignments": len(participants),
            "Attendance %": round(present / len(participants) * 100, 1) if participants else 0,
            "Status": employee.get("status", ""),
        })

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()) if rows else ["Employee ID","Name","Department","Designation","Reporting Manager","Training Assignments","Attendance %","Status"])
    writer.writeheader()
    writer.writerows(rows)
    return Response(out.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition": "attachment; filename=employee-training-report.csv"
    })
