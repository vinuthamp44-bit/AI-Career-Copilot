import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    APP_ENV = os.getenv("APP_ENV", "development")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_CACHE_MINUTES = int(os.getenv("GITHUB_CACHE_MINUTES", "30"))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///career_copilot.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    ALLOWED_EXTENSIONS = {"pdf"}
