import os

from flask import Flask, render_template

from app.config import Config
from app.extensions import db


NAV_ITEMS = [
    {
        "endpoint": "pages.backlog",
        "label": "Meu Backlog",
        "short_label": "Backlog",
        "icon": "M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 13h8v8h-8z",
    },
    {
        "endpoint": "pages.run_form",
        "label": "Registrar Run",
        "short_label": "Nova Run",
        "icon": "M13 2L3 14h6l-1 8 11-14h-7z",
    },
    {
        "endpoint": "pages.runs",
        "label": "Minhas Runs",
        "short_label": "Runs",
        "icon": "M4 5h16v2H4zm0 6h16v2H4zm0 6h10v2H4z",
    },
    {
        "endpoint": "pages.builds",
        "label": "Minhas Builds",
        "short_label": "Builds",
        "icon": "M22 6.5a4.5 4.5 0 01-6.36 4.1L9.5 16.7a2 2 0 11-2.83-2.83l6.1-6.14A4.5 4.5 0 1122 6.5z",
    },
]


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(config_class)

    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)

    _registrar_blueprints(app)
    _registrar_error_handlers(app)
    _registrar_context_processors(app)

    with app.app_context():
        from app import models  
        db.create_all()

    return app


def _registrar_blueprints(app):
    from app.routes.pages import pages_bp
    from app.routes.auth import auth_bp
    from app.routes.api_jogos import api_jogos_bp
    from app.routes.api_runs import api_runs_bp
    from app.routes.api_builds import api_builds_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_jogos_bp)
    app.register_blueprint(api_runs_bp)
    app.register_blueprint(api_builds_bp)


def _registrar_error_handlers(app):
    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def erro_interno(_erro):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _registrar_context_processors(app):
    @app.context_processor
    def injetar_globais():
        from app.utils.auth import usuario_atual

        return {"nav_items": NAV_ITEMS, "usuario_logado": usuario_atual()}
