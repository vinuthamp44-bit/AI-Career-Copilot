import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db
from routes.api import api


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.init_app(app)
    JWTManager(app)
    origins = [origin.strip() for origin in os.getenv("FRONTEND_URL", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5175,http://127.0.0.1:5175").split(",")]
    CORS(app, resources={r"/api/*": {"origins": origins, "allow_headers": ["Content-Type", "Authorization"]}})
    app.register_blueprint(api)
    with app.app_context():
        db.create_all()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
