from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from db import db

departments_bp = Blueprint("departments", __name__, url_prefix="/api/departments")

DEPARTMENTS = ["HR", "Management", "Finance", "Maintenance", "Production", "QA / Quality", "Stores", "OQC"]

@departments_bp.get("")
@jwt_required()
def list_departments():
    rows = []
    for name in DEPARTMENTS:
        employees = list(db.employees.find({"department": name, "status": {"$ne": "Inactive"}}, {"employeeId": 1, "name": 1, "_id": 0}))
        ids = [x["employeeId"] for x in employees]
        participants = list(db.training_participants.find({"employeeId": {"$in": ids}})) if ids else []
        training_ids = list({p.get("trainingId") for p in participants if p.get("trainingId")})
        from bson import ObjectId
        tids = [ObjectId(x) for x in training_ids if ObjectId.is_valid(x)]
        ongoing = db.trainings.count_documents({"_id": {"$in": tids}, "status": {"$nin": ["Completed", "Cancelled"]}}) if tids else 0
        attendance_marked = sum(1 for p in participants if p.get("attendance") in {"Present", "Absent", "Partial"})
        feedback_submitted = db.feedback.count_documents({"employeeId": {"$in": ids}, "status": "Submitted"}) if ids else 0
        rows.append({"_id": name.lower().replace(" ", "-").replace("/", "-"), "name": name, "status": "Active", "employeeCount": len(employees), "ongoingTrainings": ongoing, "attendanceMarked": attendance_marked, "attendancePending": max(0, len(participants)-attendance_marked), "feedbackSubmitted": feedback_submitted, "feedbackPending": max(0, len(participants)-feedback_submitted)})
    return jsonify(rows)

@departments_bp.get("/<path:name>")
@jwt_required()
def department_detail(name):
    if name not in DEPARTMENTS:
        return jsonify({"message": "Department not found"}), 404
    employees = list(db.employees.find({"department": name, "status": {"$ne": "Inactive"}}, {"employeeId": 1, "name": 1, "designation": 1, "_id": 0}).sort("name", 1))
    ids = [e["employeeId"] for e in employees]
    participants = list(db.training_participants.find({"employeeId": {"$in": ids}})) if ids else []
    tids = list({p.get("trainingId") for p in participants if p.get("trainingId")})
    from bson import ObjectId
    objids = [ObjectId(x) for x in tids if ObjectId.is_valid(x)]
    trainings = list(db.trainings.find({"_id": {"$in": objids}}).sort("startDate", -1)) if objids else []
    ongoing = [t for t in trainings if t.get("status") not in {"Completed", "Cancelled"}]
    att_marked = sum(1 for p in participants if p.get("attendance") in {"Present", "Absent", "Partial"})
    feedback_submitted = sum(1 for p in participants if p.get("feedbackStatus") == "Submitted")
    return jsonify({
        "name": name,
        "employeeCount": len(employees),
        "employees": employees,
        "ongoingTrainings": [{"_id": str(t["_id"]), "title": t.get("title",""), "startDate": t.get("startDate", t.get("trainingDate")), "endDate": t.get("endDate", t.get("startDate"))} for t in ongoing],
        "attendance": {"marked": att_marked, "pending": max(0, len(participants)-att_marked)},
        "feedback": {"submitted": feedback_submitted, "pending": max(0, len(participants)-feedback_submitted)}
    })

@departments_bp.post("")
@jwt_required()
def create_department():
    return jsonify({"message": "Departments are fixed and cannot be added."}), 403

@departments_bp.put("/<path:department_id>")
@jwt_required()
def update_department(department_id):
    return jsonify({"message": "Departments are fixed and cannot be edited."}), 403
