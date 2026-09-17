import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/employee_training")
MONGO_DB = os.getenv("MONGO_DB", "employee_training")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "92dfe91887a9b4b69be14a1ef17582137e092623ab00c3bf60cadcbbf0d9907c")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://employeetrainingmanagement-1.onrender.com/api")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

# The first HR account is created only if these values are supplied.
ADMIN_EMPLOYEE_ID = os.getenv("ADMIN_EMPLOYEE_ID", "HR001")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_NAME = os.getenv("ADMIN_NAME", "HR Administrator")
ADMIN_DEPARTMENT = os.getenv("ADMIN_DEPARTMENT", "HR")
