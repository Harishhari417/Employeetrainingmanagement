import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "employee_training")

FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173"
)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

ADMIN_EMPLOYEE_ID = os.getenv("ADMIN_EMPLOYEE_ID")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Administrator")
ADMIN_DEPARTMENT = os.getenv("ADMIN_DEPARTMENT", "HR")