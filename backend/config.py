import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB", "employee_training")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    JWT_ACCESS_TOKEN_EXPIRES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "7200")
    )

    # Frontend
    FRONTEND_ORIGIN = os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5173"
    )

    # Temporary/admin configuration
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
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "")

    VERIFICATION_CODE_EXPIRES_MINUTES = int(os.getenv("VERIFICATION_CODE_EXPIRES_MINUTES", "10"))
    MONTHLY_REPORT_ENABLED = os.getenv("MONTHLY_REPORT_ENABLED", "true").lower() == "true"
    MONTHLY_REPORT_DAY = int(os.getenv("MONTHLY_REPORT_DAY", "1"))
    MONTHLY_REPORT_HOUR = int(os.getenv("MONTHLY_REPORT_HOUR", "9"))