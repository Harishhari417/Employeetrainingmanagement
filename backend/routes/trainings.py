from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from db import db


trainings_bp = Blueprint(
    "trainings",
    __name__,
    url_prefix="/api/trainings"
)


@trainings_bp.get("/progress")
@jwt_required()
def training_progress():

    try:
        # ---------------------------------------------------------
        # GET LOGGED-IN USER
        # ---------------------------------------------------------
        claims = get_jwt()

        role = claims.get("role")
        employee_id = claims.get("employeeId")
        department = claims.get("department")

        # ---------------------------------------------------------
        # CHECK ROLE
        # ---------------------------------------------------------
        if role not in {
            "HR_ADMIN",
            "MANAGER",
            "EMPLOYEE"
        }:
            return jsonify({
                "message": "Invalid user role"
            }), 403

        # ---------------------------------------------------------
        # FIND EMPLOYEES VISIBLE TO THIS USER
        # ---------------------------------------------------------
        if role == "HR_ADMIN":

            employee_filter = {}

        elif role == "MANAGER":

            employee_filter = {
                "department": department
            }

        else:

            employee_filter = {
                "employeeId": employee_id
            }

        employees = list(
            db.employees.find(
                employee_filter,
                {
                    "_id": 0,
                    "employeeId": 1,
                    "name": 1,
                    "employeeName": 1,
                    "department": 1,
                },
            )
        )

        employee_map = {}

        for employee in employees:

            employee_id_value = employee.get(
                "employeeId"
            )

            if not employee_id_value:
                continue

            employee_map[employee_id_value] = {
                "employeeId": employee_id_value,
                "employeeName": (
                    employee.get("employeeName")
                    or employee.get("name")
                    or employee_id_value
                ),
                "department": employee.get(
                    "department",
                    ""
                ),
            }

        # ---------------------------------------------------------
        # FIND ASSIGNMENTS
        # ---------------------------------------------------------
        employee_ids = list(
            employee_map.keys()
        )

        if not employee_ids:
            return jsonify([]), 200

        participant_filter = {
            "employeeId": {
                "$in": employee_ids
            }
        }

        participants = list(
            db.training_participants.find(
                participant_filter,
                {
                    "_id": 0
                },
            )
        )

        result = []

        # ---------------------------------------------------------
        # BUILD TRAINING PROGRESS
        # ---------------------------------------------------------
        for participant in participants:

            employee_id_value = participant.get(
                "employeeId"
            )

            employee = employee_map.get(
                employee_id_value
            )

            if not employee:
                continue

            training_id = participant.get(
                "trainingId"
            )

            if training_id is None:
                continue

            # -----------------------------------------------------
            # FIND TRAINING
            # -----------------------------------------------------
            training = db.trainings.find_one(
                {
                    "$or": [
                        {
                            "trainingId": training_id
                        },
                        {
                            "_id": training_id
                        },
                    ]
                },
                {
                    "_id": 0,
                    "title": 1,
                    "trainingTitle": 1,
                    "name": 1,
                },
            )

            if not training:
                continue

            training_title = (
                training.get("trainingTitle")
                or training.get("title")
                or training.get("name")
                or "Training"
            )

            # -----------------------------------------------------
            # ATTENDANCE
            # -----------------------------------------------------
            attendance = db.attendance.find_one(
                {
                    "trainingId": training_id,
                    "employeeId": employee_id_value,
                },
                sort=[
                    (
                        "updatedAt",
                        -1,
                    )
                ],
            )

            attendance_status = (
                attendance.get("status")
                if attendance
                else "Not Marked"
            )

            # -----------------------------------------------------
            # FEEDBACK
            # -----------------------------------------------------
            feedback = db.feedback.find_one(
                {
                    "trainingId": training_id,
                    "employeeId": employee_id_value,
                },
                {
                    "_id": 1,
                },
            )

            if feedback:
                feedback_status = "Submitted"
            else:
                feedback_status = (
                    participant.get(
                        "feedbackStatus"
                    )
                    or "Pending"
                )

            # -----------------------------------------------------
            # COMPLETION
            # -----------------------------------------------------
            completion_status = (
                participant.get(
                    "completionStatus"
                )
                or participant.get("status")
                or "Assigned"
            )

            # -----------------------------------------------------
            # RESULT
            # -----------------------------------------------------
            result.append({
                "trainingId": str(
                    training_id
                ),
                "trainingTitle": training_title,
                "employeeId": employee_id_value,
                "employeeName": employee[
                    "employeeName"
                ],
                "department": employee[
                    "department"
                ],
                "attendance": attendance_status,
                "completionStatus": completion_status,
                "feedbackStatus": feedback_status,
                "updatedAt": participant.get(
                    "updatedAt"
                ),
            })

        return jsonify(result), 200

    except Exception as e:

        print(
            "TRAINING PROGRESS ERROR:",
            str(e)
        )

        return jsonify({
            "message": "Failed to load training progress",
            "error": str(e)
        }), 500