import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/employee_training")
MONGO_DB = os.getenv("MONGO_DB", "employee_training")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://employeetrainingmanagement-2.onrender.com")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

# The first HR account is created only if these values are supplied.
ADMIN_EMPLOYEE_ID = os.getenv("ADMIN_EMPLOYEE_ID", "HR001")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_NAME = os.getenv("ADMIN_NAME", "HR Administrator")
ADMIN_DEPARTMENT = os.getenv("ADMIN_DEPARTMENT", "HR")
