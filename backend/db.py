import certifi
from pymongo import MongoClient

from config import Config


MONGO_URI = Config.MONGO_URI
MONGO_DB = Config.MONGO_DB


client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
)

db = client[MONGO_DB]


def create_indexes():
    db.users.create_index("username", unique=True)
    db.users.create_index("employeeId")
    db.employees.create_index("employeeId", unique=True)
    db.training_participants.create_index(
        [("trainingId", 1), ("employeeId", 1)],
        unique=True,
)