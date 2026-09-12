from flask import Blueprint, request, jsonify

from app.services.backlog_service import BacklogService, ErroDeValidacao, RecursoNaoEncontrado
from app.utils.auth import api_login_required, usuario_atual

api_builds_bp = Blueprint("api_builds", __name__, url_prefix="/api/builds")


@api_builds_bp.route("", methods=["GET"])
@api_login_required
def listar():
    servico = BacklogService(usuario_atual())
    return jsonify([build.to_dict() for build in servico.listar_builds()])


@api_builds_bp.route("", methods=["POST"])
@api_login_required
def criar():
    servico = BacklogService(usuario_atual())
    try:
        build = servico.registrar_build(request.get_json(silent=True) or {})
    except ErroDeValidacao as erro:
        return jsonify({"erro": str(erro)}), 400
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify(build.to_dict()), 201


@api_builds_bp.route("/<int:build_id>", methods=["DELETE"])
@api_login_required
def excluir(build_id):
    servico = BacklogService(usuario_atual())
    try:
        servico.excluir_build(build_id)
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return "", 204
