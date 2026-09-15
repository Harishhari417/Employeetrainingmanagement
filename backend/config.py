import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB", "employee_training")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    FRONTEND_ORIGIN = os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5173"
    )

    JWT_ACCESS_TOKEN_EXPIRES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600")
    )