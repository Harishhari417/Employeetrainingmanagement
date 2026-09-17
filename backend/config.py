import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # -------------------------
    # MongoDB
    # -------------------------
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB", "employee_training")

    # -------------------------
    # JWT
    # -------------------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    # Token expiration
    JWT_ACCESS_TOKEN_EXPIRES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "86400")
    )

    # -------------------------
    # Frontend
    # -------------------------
    FRONTEND_ORIGIN = os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5173"
    )

    # -------------------------
    # Admin Authentication
    # -------------------------
    # These are NOT stored in MongoDB.
    ADMIN_EMPLOYEE_ID = os.getenv("ADMIN_EMPLOYEE_ID")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_NAME = os.getenv(
        "ADMIN_NAME",
        "System Administrator"
    )
    ADMIN_DEPARTMENT = os.getenv(
        "ADMIN_DEPARTMENT",
        "HR"
    )