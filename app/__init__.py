
import os
from flask import Flask
from app.config import Config
from app.extensions import db

def create_app(config_class=Config):
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(config_class)
    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)
    db.init_app(app)
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
