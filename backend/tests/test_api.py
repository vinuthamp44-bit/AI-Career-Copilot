import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from config import Config
from models import db


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-secret"


def test_health():
    app = create_app(TestConfig)
    with app.test_client() as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json["status"] == "ok"
    with app.app_context():
        db.drop_all()


def test_register_login():
    app = create_app(TestConfig)
    with app.test_client() as client:
        response = client.post("/api/auth/register", json={"name": "Test User", "email": "test@example.com", "password": "password123"})
        assert response.status_code == 201
        assert response.json["token"]
        login = client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
        assert login.status_code == 200
    with app.app_context():
        db.drop_all()
