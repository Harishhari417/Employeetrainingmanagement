from flask import Blueprint, jsonify, request
from db import db
from models.department import build_department, serialize_department

departments_bp = Blueprint("departments", __name__, url_prefix="/api/departments")

@departments_bp.get("")
def list_departments():
    records = [serialize_department(x) for x in db.departments.find().sort("name", 1)]
    return jsonify(records)

@departments_bp.post("")
def create_department():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "").strip()
    if not name:
        return jsonify({"message": "Department name is required"}), 400
    if db.departments.find_one({"name": name}):
        return jsonify({"message": "Department already exists"}), 409
    result = db.departments.insert_one(build_department({"name": name}))
    return jsonify({"message": "Department created", "id": str(result.inserted_id)}), 201

@departments_bp.put("/<department_id>")
def update_department(department_id):
    from bson import ObjectId
    payload = request.get_json(silent=True) or {}
    updates = {k: payload[k] for k in ["name", "status"] if k in payload}
    try:
        result = db.departments.update_one({"_id": ObjectId(department_id)}, {"$set": updates})
    except Exception:
        return jsonify({"message": "Invalid department id"}), 400
    if result.matched_count == 0:
        return jsonify({"message": "Department not found"}), 404
    return jsonify({"message": "Department updated"})
