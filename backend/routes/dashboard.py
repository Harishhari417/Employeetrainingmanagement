from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from db import db

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/dashboard"
)


@dashboard_bp.get("")
@jwt_required()
def dashboard():

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
        if role not in [
            "HR_ADMIN",
            "MANAGER",
            "EMPLOYEE"
        ]:
            return jsonify({
                "message": "Invalid user role"
            }), 403

        # =========================================================
        # EMPLOYEE FILTER
        # =========================================================
        if role == "EMPLOYEE":

            employee_filter = {
                "employeeId": employee_id
            }

            participant_filter = {
                "employeeId": employee_id
            }

            attendance_filter = {
                "employeeId": employee_id
            }

            feedback_filter = {
                "employeeId": employee_id
            }

            evaluation_filter = {
                "employeeId": employee_id
            }

        # =========================================================
        # MANAGER FILTER
        # =========================================================
        elif role == "MANAGER":

            employee_filter = {
                "department": department
            }

            # Find employees belonging to manager's department
            manager_employees = list(
                db.employees.find(
                    {
                        "department": department
                    },
                    {
                        "_id": 0,
                        "employeeId": 1
                    }
                )
            )

            manager_employee_ids = [
                item.get("employeeId")
                for item in manager_employees
                if item.get("employeeId")
            ]

            participant_filter = {
                "employeeId": {
                    "$in": manager_employee_ids
                }
            }

            attendance_filter = {
                "employeeId": {
                    "$in": manager_employee_ids
                }
            }

            feedback_filter = {
                "employeeId": {
                    "$in": manager_employee_ids
                }
            }

            evaluation_filter = {
                "employeeId": {
                    "$in": manager_employee_ids
                }
            }

        # =========================================================
        # HR ADMIN
        # =========================================================
        else:

            employee_filter = {}
            participant_filter = {}
            attendance_filter = {}
            feedback_filter = {}
            evaluation_filter = {}

        # =========================================================
        # TOTAL EMPLOYEES
        # =========================================================
        total_employees = db.employees.count_documents(
            employee_filter
        )

        # =========================================================
        # TOTAL TRAININGS
        # =========================================================
        if role == "HR_ADMIN":

            total_trainings = db.trainings.count_documents({})

        else:

            # Count unique training assignments
            assignments = db.training_participants.distinct(
                "trainingId",
                participant_filter
            )

            total_trainings = len(assignments)

        # =========================================================
        # COMPLETED TRAININGS
        # =========================================================
        completed_trainings = db.training_participants.count_documents(
            {
                **participant_filter,
                "completionStatus": "Completed"
            }
        )

        # =========================================================
        # ATTENDANCE
        # =========================================================
        attendance_total = db.attendance.count_documents(
            attendance_filter
        )

        attendance_present = db.attendance.count_documents(
            {
                **attendance_filter,
                "status": {
                    "$in": [
                        "Present",
                        "present",
                        "PRESENT"
                    ]
                }
            }
        )

        if attendance_total > 0:

            attendance_percentage = round(
                (
                    attendance_present /
                    attendance_total
                ) * 100,
                2
            )

        else:

            attendance_percentage = 0

        # =========================================================
        # FEEDBACK
        # =========================================================
        feedback_count = db.feedback.count_documents(
            feedback_filter
        )

        # =========================================================
        # PENDING FEEDBACK
        # =========================================================
        pending_feedback = db.training_participants.count_documents(
            {
                **participant_filter,
                "$or": [
                    {
                        "feedbackStatus": {
                            "$exists": False
                        }
                    },
                    {
                        "feedbackStatus": {
                            "$in": [
                                "Pending",
                                "pending",
                                "Due",
                                "due",
                                "Not Submitted"
                            ]
                        }
                    }
                ]
            }
        )

        # =========================================================
        # PENDING EVALUATIONS
        # =========================================================
        pending_evaluations = db.evaluations.count_documents(
            {
                **evaluation_filter,
                "status": {
                    "$in": [
                        "Pending",
                        "pending",
                        "Due",
                        "due",
                        "Scheduled"
                    ]
                }
            }
        )

        # =========================================================
        # RESPONSE
        # =========================================================
        return jsonify({
            "totalTrainings": total_trainings,
            "completedTrainings": completed_trainings,
            "totalEmployees": total_employees,
            "attendancePercentage": attendance_percentage,
            "feedbackCount": feedback_count,
            "pendingFeedback": pending_feedback,
            "pendingEvaluations": pending_evaluations
        }), 200

    except Exception as e:

        print(
            "DASHBOARD ERROR:",
            str(e)
        )

        return jsonify({
            "message": "Failed to load dashboard",
            "error": str(e)
        }), 500