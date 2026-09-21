from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required


from db import db

trainings_bp = Blueprint(
    "trainings",
    __name__,
    url_prefix="/api/trainings"
)

trainings_collection = db["trainings"]
participants_collection = db["training_participants"]
employees_collection = db["employees"]

LOCAL_TZ = ZoneInfo("Asia/Kolkata")
LOCKED_STATUSES = ("Completed", "Cancelled")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def now_utc():
    return datetime.now(timezone.utc)


def parse_date(value):
    """
    Accepts ISO strings, including the "YYYY-MM-DDTHH:MM" value produced by
    <input type="datetime-local">. Naive values are treated as IST.
    """
    if not value:
        return None

    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LOCAL_TZ)

    return parsed


def to_object_id(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def employee_is_active(employee):
    return (employee.get("status") or "").strip().lower() != "inactive"


def clean_id_list(values):
    if not isinstance(values, list):
        return []

    return list(
        dict.fromkeys(
            str(value).strip()
            for value in values
            if value and str(value).strip()
        )
    )


def serialize_training(training, trainee_ids=None):
    if not training:
        return None

    return {
        "_id": str(training["_id"]),
        "title": training.get("title", ""),
        "content": training.get("content", ""),
        "trainingType": training.get("trainingType", ""),
        "trainerName": training.get("trainerName", ""),
        "trainerEmployeeId": training.get("trainerEmployeeId", ""),
        "trainerCategory": training.get("trainerCategory", ""),
        "venue": training.get("venue", ""),
        "trainingDate": training.get("trainingDate"),
        "trainingMode": training.get("trainingMode", ""),
        "durationMinutes": training.get("durationMinutes", 0),
        "status": training.get("status", "Upcoming"),
        "departments": training.get("departments", []),
        "traineeIds": (
            trainee_ids
            if trainee_ids is not None
            else training.get("traineeIds", [])
        ),
    }


def get_participant_ids(training_id):
    rows = participants_collection.find(
        {"trainingId": training_id},
        {"_id": 0, "employeeId": 1}
    )
    return [row["employeeId"] for row in rows if row.get("employeeId")]


def sync_participants(training_id, employee_ids):
    """
    Makes the participant collection match employee_ids exactly:
    - removes participants that are no longer assigned
    - adds new ones (existing ones keep their attendance / progress)
    - mirrors the list onto training.traineeIds
    """
    existing_ids = set(get_participant_ids(training_id))
    wanted_ids = set(employee_ids)

    to_remove = existing_ids - wanted_ids
    to_add = [eid for eid in employee_ids if eid not in existing_ids]

    if to_remove:
        participants_collection.delete_many({
            "trainingId": training_id,
            "employeeId": {"$in": list(to_remove)}
        })

    if to_add:
        timestamp = now_utc()
        participants_collection.insert_many([
            {
                "trainingId": training_id,
                "employeeId": employee_id,
                "completionStatus": "Not Started",
                "attendance": "Pending",
                "feedbackStatus": "Pending",
                "createdAt": timestamp,
                "updatedAt": timestamp,
            }
            for employee_id in to_add
        ])

    trainings_collection.update_one(
        {"_id": ObjectId(training_id)},
        {"$set": {"traineeIds": employee_ids, "updatedAt": now_utc()}}
    )


def filter_active_employee_ids(employee_ids):
    if not employee_ids:
        return []

    found = employees_collection.find(
        {"employeeId": {"$in": employee_ids}}
    )

    active = {
        employee["employeeId"]
        for employee in found
        if employee_is_active(employee)
    }

    # keep the order the client sent
    return [eid for eid in employee_ids if eid in active]


# --------------------------------------------------------------------------
# Trainings CRUD
# --------------------------------------------------------------------------

@trainings_bp.route("", methods=["GET"])
@jwt_required()
def get_trainings():
    trainings = list(trainings_collection.find().sort("trainingDate", -1))

    # one query for all participants instead of one per training
    participants_map = {}
    for row in participants_collection.find(
        {}, {"_id": 0, "trainingId": 1, "employeeId": 1}
    ):
        if row.get("trainingId") and row.get("employeeId"):
            participants_map.setdefault(
                row["trainingId"], []
            ).append(row["employeeId"])

    result = [
        serialize_training(
            training,
            participants_map.get(str(training["_id"]), [])
        )
        for training in trainings
    ]

    return jsonify(result), 200


@trainings_bp.route("", methods=["POST"])
@jwt_required()
def create_training():
    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"message": "Training title is required."}), 400

    training_date = data.get("trainingDate")
    if training_date and not parse_date(training_date):
        return jsonify({"message": "Invalid training date."}), 400

    trainer_category = data.get("trainerCategory", "Internal")
    trainer_employee_id = str(data.get("trainerEmployeeId", "") or "").strip()

    if trainer_category == "Internal" and not trainer_employee_id:
        return jsonify({
            "message": "Internal trainer must be an employee."
        }), 400

    try:
        duration = int(data.get("durationMinutes", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid duration."}), 400

    departments = data.get("departments", [])
    if not isinstance(departments, list):
        departments = []

    # Status is stored as Upcoming / Completed / Cancelled only.
    # "Ongoing" is derived by the frontend from the date.
    status = data.get("status", "Upcoming")
    if status not in ("Upcoming", "Completed", "Cancelled"):
        status = "Upcoming"

    timestamp = now_utc()

    document = {
        "title": title,
        "content": str(data.get("content", "")).strip(),
        "trainingType": data.get("trainingType", "Technical"),
        "trainerName": str(data.get("trainerName", "")).strip(),
        "trainerEmployeeId": (
            trainer_employee_id if trainer_category == "Internal" else ""
        ),
        "trainerCategory": trainer_category,
        "venue": str(data.get("venue", "")).strip(),
        "trainingDate": training_date,
        "trainingMode": data.get("trainingMode", "Offline"),
        "durationMinutes": duration,
        "status": status,
        "departments": departments,
        "traineeIds": [],
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }

    result = trainings_collection.insert_one(document)
    document["_id"] = result.inserted_id

    trainee_ids = filter_active_employee_ids(
        clean_id_list(data.get("traineeIds", []))
    )
    if trainee_ids:
        sync_participants(str(result.inserted_id), trainee_ids)
        document["traineeIds"] = trainee_ids

    return jsonify({
        "message": "Training created successfully.",
        "training": serialize_training(document)
    }), 201


@trainings_bp.route("/<training_id>", methods=["GET"])
@jwt_required()
def get_training(training_id):
    object_id = to_object_id(training_id)
    if not object_id:
        return jsonify({"message": "Invalid training ID."}), 400

    training = trainings_collection.find_one({"_id": object_id})
    if not training:
        return jsonify({"message": "Training not found."}), 404

    participants = list(
        participants_collection.find({"trainingId": training_id})
    )

    data = serialize_training(
        training,
        [p["employeeId"] for p in participants if p.get("employeeId")]
    )

    data["participants"] = [
        {
            "employeeId": item.get("employeeId", ""),
            "completionStatus": item.get("completionStatus", "Not Started"),
            "attendance": item.get("attendance", "Pending"),
            "feedbackStatus": item.get("feedbackStatus", "Pending"),
        }
        for item in participants
    ]

    return jsonify(data), 200


@trainings_bp.route("/<training_id>", methods=["PUT"])
@jwt_required()
def update_training(training_id):
    object_id = to_object_id(training_id)
    if not object_id:
        return jsonify({"message": "Invalid training ID."}), 400

    data = request.get_json(silent=True) or {}

    allowed_fields = [
        "title", "content", "trainingType", "trainerName",
        "trainerEmployeeId", "trainerCategory", "venue", "trainingDate",
        "trainingMode", "durationMinutes", "status", "departments",
    ]

    update_data = {f: data[f] for f in allowed_fields if f in data}

    if not update_data:
        return jsonify({"message": "No fields to update."}), 400

    if "trainingDate" in update_data and update_data["trainingDate"]:
        if not parse_date(update_data["trainingDate"]):
            return jsonify({"message": "Invalid training date."}), 400

    if "durationMinutes" in update_data:
        try:
            update_data["durationMinutes"] = int(
                update_data["durationMinutes"] or 0
            )
        except (TypeError, ValueError):
            return jsonify({"message": "Invalid duration."}), 400

    update_data["updatedAt"] = now_utc()

    result = trainings_collection.update_one(
        {"_id": object_id}, {"$set": update_data}
    )

    if result.matched_count == 0:
        return jsonify({"message": "Training not found."}), 404

    training = trainings_collection.find_one({"_id": object_id})

    return jsonify({
        "message": "Training updated successfully.",
        "training": serialize_training(
            training, get_participant_ids(training_id)
        )
    }), 200


@trainings_bp.route("/<training_id>", methods=["DELETE"])
@jwt_required()
def delete_training(training_id):
    object_id = to_object_id(training_id)
    if not object_id:
        return jsonify({"message": "Invalid training ID."}), 400

    result = trainings_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        return jsonify({"message": "Training not found."}), 404

    participants_collection.delete_many({"trainingId": training_id})

    return jsonify({"message": "Training deleted successfully."}), 200


# --------------------------------------------------------------------------
# Assignment
# --------------------------------------------------------------------------

@trainings_bp.route("/<training_id>/participants", methods=["PUT"])
@jwt_required()
def update_participants(training_id):
    object_id = to_object_id(training_id)
    if not object_id:
        return jsonify({"message": "Invalid training ID."}), 400

    training = trainings_collection.find_one({"_id": object_id})
    if not training:
        return jsonify({"message": "Training not found."}), 404

    if training.get("status") in LOCKED_STATUSES:
        return jsonify({
            "message": f"Cannot change participants of a "
                       f"{training['status'].lower()} training."
        }), 400

    data = request.get_json(silent=True) or {}
    raw_ids = data.get("employeeIds", [])

    if not isinstance(raw_ids, list):
        return jsonify({"message": "employeeIds must be an array."}), 400

    valid_ids = filter_active_employee_ids(clean_id_list(raw_ids))

    sync_participants(training_id, valid_ids)

    return jsonify({
        "message": "Training assigned successfully.",
        "trainingId": training_id,
        "employeeIds": valid_ids,
        "count": len(valid_ids),
        "skipped": len(clean_id_list(raw_ids)) - len(valid_ids),
    }), 200


# --------------------------------------------------------------------------
# Complete / Cancel
# --------------------------------------------------------------------------

@trainings_bp.route("/<training_id>/complete", methods=["POST"])
@jwt_required()
def complete_training(training_id):
    object_id = to_object_id(training_id)
    if not object_id:
        return jsonify({"message": "Invalid training ID."}), 400

    training = trainings_collection.find_one({"_id": object_id})
    if not training:
        return jsonify({"message": "Training not found."}), 404

    if training.get("status") == "Cancelled":
        return jsonify({
            "message": "A cancelled training cannot be completed."
        }), 400

    timestamp = now_utc()

    trainings_collection.update_one(
        {"_id": object_id},
        {"$set": {"status": "Completed", "updatedAt": timestamp}}
    )

    participants_collection.update_many(
        {"trainingId": training_id},
        {"$set": {"completionStatus": "Completed", "updatedAt": timestamp}}
    )

    updated = trainings_collection.find_one({"_id": object_id})

    return jsonify({
        "message": "Training completed successfully.",
        "training": serialize_training(
            updated, get_participant_ids(training_id)
        )
    }), 200


@trainings_bp.route("/<training_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_training(training_id):
    object_id = to_object_id(training_id)
    if not object_id:
        return jsonify({"message": "Invalid training ID."}), 400

    training = trainings_collection.find_one({"_id": object_id})
    if not training:
        return jsonify({"message": "Training not found."}), 404

    if training.get("status") == "Completed":
        return jsonify({
            "message": "A completed training cannot be cancelled."
        }), 400

    trainings_collection.update_one(
        {"_id": object_id},
        {"$set": {"status": "Cancelled", "updatedAt": now_utc()}}
    )

    updated = trainings_collection.find_one({"_id": object_id})

    return jsonify({
        "message": "Training cancelled successfully.",
        "training": serialize_training(
            updated, get_participant_ids(training_id)
        )
    }), 200


# --------------------------------------------------------------------------
# Progress
# NOTE: static route "/progress" is declared before dynamic routes that could
# shadow it; Flask matches static segments first, so this is safe.
# --------------------------------------------------------------------------

@trainings_bp.route("/progress", methods=["GET"])
@jwt_required()
def get_training_progress():
    claims = get_jwt()

    role = claims.get("role")
    employee_id = claims.get("employeeId")
    department = claims.get("department")

    query = {}
    if role == "EMPLOYEE":
        query["employeeId"] = employee_id

    participants = list(participants_collection.find(query))

    # batch-load related trainings and employees
    training_ids = {
        to_object_id(p.get("trainingId"))
        for p in participants
        if to_object_id(p.get("trainingId"))
    }
    employee_ids = {
        p.get("employeeId") for p in participants if p.get("employeeId")
    }

    trainings_map = {
        str(t["_id"]): t
        for t in trainings_collection.find({"_id": {"$in": list(training_ids)}})
    }
    employees_map = {
        e["employeeId"]: e
        for e in employees_collection.find(
            {"employeeId": {"$in": list(employee_ids)}}
        )
    }

    result = []

    for participant in participants:
        training = trainings_map.get(participant.get("trainingId"))
        employee = employees_map.get(participant.get("employeeId"))

        if not training or not employee:
            continue

        if (
            role == "MANAGER"
            and department
            and employee.get("department") != department
        ):
            continue

        result.append({
            "trainingId": str(training["_id"]),
            "trainingTitle": training.get("title", ""),
            "employeeId": participant.get("employeeId"),
            "employeeName": employee.get(
                "name", employee.get("employeeName", "")
            ),
            "department": employee.get("department", ""),
            "attendance": participant.get("attendance", "Pending"),
            "completionStatus": participant.get(
                "completionStatus", "Not Started"
            ),
            "feedbackStatus": participant.get("feedbackStatus", "Pending"),
            "updatedAt": participant.get("updatedAt"),
        })

    return jsonify(result), 200


@trainings_bp.route("/<training_id>/progress", methods=["PUT"])
@jwt_required()
def update_training_progress(training_id):
    if not to_object_id(training_id):
        return jsonify({"message": "Invalid training ID."}), 400

    data = request.get_json(silent=True) or {}

    employee_id = data.get("employeeId")
    if not employee_id:
        return jsonify({"message": "employeeId is required."}), 400

    update_fields = {}
    for field in ("completionStatus", "attendance", "feedbackStatus"):
        if data.get(field):
            update_fields[field] = data[field]

    if not update_fields:
        return jsonify({
            "message": "Provide completionStatus, attendance or feedbackStatus."
        }), 400

    update_fields["updatedAt"] = now_utc()

    result = participants_collection.update_one(
        {"trainingId": training_id, "employeeId": employee_id},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return jsonify({
            "message": "Employee is not assigned to this training."
        }), 404

    return jsonify({
        "message": "Training progress updated successfully."
    }), 200