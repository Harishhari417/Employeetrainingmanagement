
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from db import db
from bson import ObjectId

departments_bp = Blueprint("departments", __name__, url_prefix="/api/departments")
DEPARTMENTS = ["HR", "Management", "Finance", "Maintenance", "Production", "QA / Quality", "Stores", "OQC"]


@departments_bp.get("")
@jwt_required()
def list_departments():
    employees = list(db.employees.find(
        {"status": {"$ne": "Inactive"}, "department": {"$in": DEPARTMENTS}},
        {"employeeId": 1, "department": 1, "_id": 0}
    ))
    ids_by_dept = {name: [] for name in DEPARTMENTS}
    all_ids = []
    for employee in employees:
        dept = employee.get("department")
        eid = employee.get("employeeId")
        if dept in ids_by_dept and eid:
            ids_by_dept[dept].append(eid)
            all_ids.append(eid)

    participants = list(db.training_participants.find(
        {"employeeId": {"$in": all_ids}},
        {"trainingId": 1, "employeeId": 1, "attendance": 1, "feedbackStatus": 1, "_id": 0}
    )) if all_ids else []

    training_ids = {p.get("trainingId") for p in participants if p.get("trainingId") and ObjectId.is_valid(p.get("trainingId"))}
    trainings = list(db.trainings.find(
        {"_id": {"$in": [ObjectId(x) for x in training_ids]}},
        {"status": 1, "startDate": 1, "endDate": 1, "departments": 1, "_id": 1}
    )) if training_ids else []

    training_map = {str(t["_id"]): t for t in trainings}
    rows = []
    for name in DEPARTMENTS:
        dept_ids = set(ids_by_dept[name])
        dept_participants = [p for p in participants if p.get("employeeId") in dept_ids]
        ongoing_ids = {
            p.get("trainingId") for p in dept_participants
            if p.get("trainingId") in training_map and training_map[p.get("trainingId")].get("status") not in {"Completed", "Cancelled"}
        }
        marked = sum(1 for p in dept_participants if p.get("attendance") in {"Present", "Absent", "Partial"})
        submitted = sum(1 for p in dept_participants if p.get("feedbackStatus") == "Submitted")
        rows.append({
            "_id": name.lower().replace(" ", "-").replace("/", "-"),
            "name": name,
            "status": "Active",
            "employeeCount": len(dept_ids),
            "ongoingTrainings": len(ongoing_ids),
            "attendanceMarked": marked,
            "attendancePending": max(0, len(dept_participants) - marked),
            "feedbackSubmitted": submitted,
            "feedbackPending": max(0, len(dept_participants) - submitted),
        })
    return jsonify(rows)


@departments_bp.get("/<path:name>")
@jwt_required()
def department_detail(name):
    if name not in DEPARTMENTS:
        return jsonify({"message": "Department not found"}), 404

    employees = list(db.employees.find(
        {"department": name, "status": {"$ne": "Inactive"}},
        {"employeeId": 1, "name": 1, "designation": 1, "_id": 0}
    ).sort("name", 1))
    ids = [e["employeeId"] for e in employees]
    participants = list(db.training_participants.find(
        {"employeeId": {"$in": ids}},
        {"trainingId": 1, "employeeId": 1, "attendance": 1, "feedbackStatus": 1, "_id": 0}
    )) if ids else []
    tids = {p.get("trainingId") for p in participants if p.get("trainingId") and ObjectId.is_valid(p.get("trainingId"))}
    trainings = list(db.trainings.find(
        {"_id": {"$in": [ObjectId(x) for x in tids]}},
        {"title": 1, "startDate": 1, "endDate": 1, "status": 1, "_id": 1}
    )) if tids else []
    ongoing = [t for t in trainings if t.get("status") not in {"Completed", "Cancelled"}]
    att_marked = sum(1 for p in participants if p.get("attendance") in {"Present", "Absent", "Partial"})
    feedback_submitted = sum(1 for p in participants if p.get("feedbackStatus") == "Submitted")
    return jsonify({
        "name": name, "employeeCount": len(employees), "employees": employees,
        "ongoingTrainings": [
            {"_id": str(t["_id"]), "title": t.get("title", ""),
             "startDate": t.get("startDate"), "endDate": t.get("endDate")}
            for t in ongoing
        ],
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
