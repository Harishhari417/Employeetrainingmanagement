from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required
from db import db

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

COLLECTIONS = {
    "employees": "Employees",
    "trainings": "Trainings",
    "departments": "Departments",
    "training_participants": "Training Participants / Attendance",
    "feedback": "Feedback",
    "evaluations": "Evaluations",
    "effectiveness_evaluations": "Effectiveness Evaluations",
    "notifications": "Notifications",
}


def admin_required():
    return get_jwt().get("role") == "HR_ADMIN"


def json_safe(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items() if key not in {"passwordHash", "password"}}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def get_collection(name):
    if name not in COLLECTIONS:
        return None
    return db[name]


def document_filter(document_id):
    try:
        return {"_id": ObjectId(document_id)}
    except (InvalidId, TypeError):
        return {"_id": document_id}


@admin_bp.get("/collections")
@jwt_required()
def list_collections():
    if not admin_required():
        return jsonify({"message": "HR Admin permission required"}), 403
    return jsonify([
        {"key": key, "label": label, "count": db[key].count_documents({})}
        for key, label in COLLECTIONS.items()
    ]), 200


@admin_bp.get("/data/<collection_name>")
@jwt_required()
def list_records(collection_name):
    if not admin_required():
        return jsonify({"message": "HR Admin permission required"}), 403
    collection = get_collection(collection_name)
    if collection is None:
        return jsonify({"message": "Collection is not available for management"}), 404
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 50))))
        search = request.args.get("search", "").strip()
        query = {}
        if search:
            query = {"$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"employeeId": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"title": {"$regex": search, "$options": "i"}},
                {"trainingName": {"$regex": search, "$options": "i"}},
            ]}
        total = collection.count_documents(query)
        records = list(collection.find(query).sort("_id", -1).skip((page - 1) * limit).limit(limit))
        return jsonify({"records": [json_safe(item) for item in records], "total": total, "page": page, "limit": limit}), 200
    except Exception as error:
        return jsonify({"message": "Unable to load records", "error": str(error)}), 500


@admin_bp.post("/data/<collection_name>")
@jwt_required()
def create_record(collection_name):
    if not admin_required():
        return jsonify({"message": "HR Admin permission required"}), 403
    collection = get_collection(collection_name)
    if collection is None:
        return jsonify({"message": "Collection is not available for management"}), 404
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        return jsonify({"message": "A JSON object with record fields is required"}), 400
    payload.pop("_id", None)
    payload.pop("passwordHash", None)
    payload.pop("password", None)
    now = datetime.now(timezone.utc)
    payload.setdefault("createdAt", now)
    payload["updatedAt"] = now
    try:
        result = collection.insert_one(payload)
        return jsonify({"message": "Record created", "id": str(result.inserted_id)}), 201
    except Exception as error:
        return jsonify({"message": "Unable to create record", "error": str(error)}), 400


@admin_bp.put("/data/<collection_name>/<record_id>")
@jwt_required()
def update_record(collection_name, record_id):
    if not admin_required():
        return jsonify({"message": "HR Admin permission required"}), 403
    collection = get_collection(collection_name)
    if collection is None:
        return jsonify({"message": "Collection is not available for management"}), 404
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"message": "A JSON object with record fields is required"}), 400
    payload.pop("_id", None)
    payload.pop("passwordHash", None)
    payload.pop("password", None)
    payload["updatedAt"] = datetime.now(timezone.utc)
    try:
        result = collection.update_one(document_filter(record_id), {"$set": payload})
        if not result.matched_count:
            return jsonify({"message": "Record not found"}), 404
        return jsonify({"message": "Record updated"}), 200
    except Exception as error:
        return jsonify({"message": "Unable to update record", "error": str(error)}), 400


@admin_bp.delete("/data/<collection_name>/<record_id>")
@jwt_required()
def delete_record(collection_name, record_id):
    if not admin_required():
        return jsonify({"message": "HR Admin permission required"}), 403
    collection = get_collection(collection_name)
    if collection is None:
        return jsonify({"message": "Collection is not available for management"}), 404
    try:
        result = collection.delete_one(document_filter(record_id))
        if not result.deleted_count:
            return jsonify({"message": "Record not found"}), 404
        return jsonify({"message": "Record deleted"}), 200
    except Exception as error:
        return jsonify({"message": "Unable to delete record", "error": str(error)}), 400
