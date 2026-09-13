from flask import Blueprint, jsonify

from app.services.backlog_service import BacklogService
from app.utils.auth import api_login_required, usuario_atual

api_estatisticas_bp = Blueprint("api_estatisticas", __name__, url_prefix="/api/estatisticas")


@api_estatisticas_bp.route("", methods=["GET"])
@api_login_required
def obter():
    servico = BacklogService(usuario_atual())
    return jsonify(servico.calcular_estatisticas_dashboard())
