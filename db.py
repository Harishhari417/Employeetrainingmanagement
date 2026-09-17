import certifi
from pymongo import MongoClient

from config import Config


client = MongoClient(
    Config.MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
)

db = client[Config.MONGO_DB]


def create_indexes():
    db.employees.create_index(
        "employeeId",
        unique=True
    )

    db.training_participants.create_index(
        [
            ("trainingId", 1),
            ("employeeId", 1)
        ],
        unique=True,
    )