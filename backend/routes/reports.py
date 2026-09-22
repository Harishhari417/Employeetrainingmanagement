import csv
import io
from flask import Blueprint, Response, request
from flask_jwt_extended import jwt_required, get_jwt
from db import db

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def training_query_from_request(claims):
    query = {}
    training_id = request.args.get("trainingId", "").strip()
    department = request.args.get("department", "").strip()
    start_date = request.args.get("startDate", "").strip()
    end_date = request.args.get("endDate", "").strip()
    if training_id:
        from bson import ObjectId
        if ObjectId.is_valid(training_id):
            query["_id"] = ObjectId(training_id)
    if claims.get("role") == "MANAGER":
        query["departments"] = claims.get("department")
    elif department:
        query["departments"] = department
    date_range = {}
    if start_date:
        date_range["$gte"] = start_date
    if end_date:
        date_range["$lte"] = end_date + ("T23:59:59" if len(end_date) == 10 else "")
    if date_range:
        query["trainingDate"] = date_range
    return query


@reports_bp.get("/training")
@jwt_required()
def training_report():
    claims = get_jwt()
    if claims.get("role") not in {"HR_ADMIN", "MANAGER"}:
        return {"message": "Manager or HR Admin permission required"}, 403
    rows = []
    for training in db.trainings.find(training_query_from_request(claims)).sort("trainingDate", 1):
        tid = str(training["_id"])
        participants = list(db.training_participants.find({"trainingId": tid}))
        present = sum(1 for p in participants if p.get("attendance") == "Present")
        feedback = list(db.feedback.find({"trainingId": tid, "status": "Submitted"}))
        evaluations = list(db.effectiveness_evaluations.find({"trainingId": tid}))
        rows.append({
            "Training ID": tid,
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
            "Evaluations": len(evaluations),
        })
    out = io.StringIO()
    fields = list(rows[0].keys()) if rows else ["Training ID", "Training", "Type", "Trainer", "Date", "Venue", "Status", "Participants", "Present", "Attendance %", "Feedback Responses", "Evaluations"]
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=training-report.csv"})


@reports_bp.get("/employees")
@jwt_required()
def employee_report():
    if get_jwt().get("role") != "HR_ADMIN":
        return {"message": "HR Admin permission required"}, 403
    rows = []
    for employee in db.employees.find().sort("name", 1):
        employee_id = employee.get("employeeId")
        participants = list(db.training_participants.find({"employeeId": employee_id}))
        present = sum(1 for p in participants if p.get("attendance") == "Present")
        rows.append({"Employee ID": employee_id, "Name": employee.get("name", ""), "Department": employee.get("department", ""), "Designation": employee.get("designation", ""), "Reporting Manager": employee.get("reportingManager", ""), "Training Assignments": len(participants), "Attendance %": round(present / len(participants) * 100, 1) if participants else 0, "Status": employee.get("status", "")})
    out = io.StringIO(); fields = list(rows[0].keys()) if rows else ["Employee ID", "Name", "Department", "Designation", "Reporting Manager", "Training Assignments", "Attendance %", "Status"]
    writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=employee-training-report.csv"})
