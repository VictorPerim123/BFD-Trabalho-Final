import logging
import os

from flask import Flask, jsonify, render_template, request
from sqlalchemy.exc import SQLAlchemyError

from app.config import Config
from app.extensions import csrf, db, migrate


NAV_ITEMS = [
    {
        "endpoint": "pages.dashboard",
        "label": "Dashboard",
        "short_label": "Painel",
        "icon": "M12 3l9 8h-3v9h-5v-6H11v6H6v-9H3z",
    },
    {
        "endpoint": "pages.backlog",
        "label": "Meu Backlog",
        "short_label": "Backlog",
        "icon": "M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 13h8v8h-8z",
    },
    {
        "endpoint": "pages.jornada",
        "label": "Jornada",
        "short_label": "Jornada",
        "icon": "M4 19h16v2H4zm1-4 4-4 3 3 6-7 1.5 1.3-7.4 8.6-3-3L6.4 16.4z",
    },
    {
        "endpoint": "pages.desafios",
        "label": "Desafios",
        "short_label": "Metas",
        "icon": "M12 2a10 10 0 1010 10A10 10 0 0012 2zm0 4a6 6 0 11-6 6 6 6 0 016-6zm0 3a3 3 0 103 3 3 3 0 00-3-3z",
    },
]


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(config_class)

    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    _configurar_logs(app)
    _registrar_blueprints(app)
    _registrar_error_handlers(app)
    _registrar_context_processors(app)
    _registrar_cabecalhos_seguranca(app)

    return app


def _registrar_blueprints(app):
    from app.routes.pages import pages_bp
    from app.routes.auth import auth_bp
    from app.routes.api_jogos import api_jogos_bp
    from app.routes.api_runs import api_runs_bp
    from app.routes.api_builds import api_builds_bp
    from app.routes.api_estatisticas import api_estatisticas_bp
    from app.routes.api_desafios import api_desafios_bp
    from app.routes.steam import steam_bp
    from app.routes.export import export_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_jogos_bp)
    app.register_blueprint(api_runs_bp)
    app.register_blueprint(api_builds_bp)
    app.register_blueprint(api_estatisticas_bp)
    app.register_blueprint(api_desafios_bp)
    app.register_blueprint(steam_bp)
    app.register_blueprint(export_bp)


def _configurar_logs(app):
    nivel = logging.DEBUG if app.debug or app.testing else logging.INFO
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(nivel)


def _registrar_error_handlers(app):
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def csrf_invalido(_erro):
        app.logger.warning("Requisição rejeitada por CSRF: %s %s", request.method, request.path)
        if request.path.startswith("/api/"):
            return jsonify({"erro": "Token CSRF ausente ou expirado."}), 400
        return render_template("errors/403.html"), 403

    @app.errorhandler(403)
    def acesso_negado(_erro):
        return render_template("errors/403.html"), 403

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

        try:
            usuario = usuario_atual()
        except SQLAlchemyError:
            db.session.rollback()
            usuario = None
        return {"nav_items": NAV_ITEMS, "usuario_logado": usuario}


def _registrar_cabecalhos_seguranca(app):
    @app.after_request
    def adicionar_cabecalhos(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resposta
