import os
import unittest

os.environ.setdefault("MONGO_URI", "mongodb://127.0.0.1:27017/employee_training_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-that-is-at-least-32-characters")
os.environ.setdefault("MONGO_DB", "employee_training_test")

from run import app


class HealthEndpointTests(unittest.TestCase):
    def test_health_endpoint_is_public_and_healthy(self):
        client = app.test_client()
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
