import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

_client = None
_db = None


def get_db():
    global _client, _db

    if _db is not None:
        return _db

    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        raise RuntimeError("MONGO_URI environment variable is not configured")

    db_name = os.getenv("MONGO_DB", "employee_training")

    _client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
    )

    # Force connection immediately so configuration problems
    # are detected clearly.
    _client.admin.command("ping")

    _db = _client[db_name]

    return _db