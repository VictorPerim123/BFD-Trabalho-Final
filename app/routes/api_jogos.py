from flask import Blueprint, request, jsonify

from app.services.backlog_service import BacklogService, ErroDeValidacao, RecursoNaoEncontrado
from app.utils.auth import api_login_required, usuario_atual

api_jogos_bp = Blueprint("api_jogos", __name__, url_prefix="/api/jogos")


@api_jogos_bp.route("", methods=["GET"])
@api_login_required
def listar():
    servico = BacklogService(usuario_atual())
    return jsonify([jogo.to_dict() for jogo in servico.listar_jogos()])


@api_jogos_bp.route("", methods=["POST"])
@api_login_required
def criar():
    servico = BacklogService(usuario_atual())
    try:
        jogo = servico.criar_jogo(request.get_json(silent=True) or {})
    except ErroDeValidacao as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify(jogo.to_dict()), 201


@api_jogos_bp.route("/<int:jogo_id>", methods=["PUT"])
@api_login_required
def atualizar(jogo_id):
    servico = BacklogService(usuario_atual())
    try:
        jogo = servico.atualizar_jogo(jogo_id, request.get_json(silent=True) or {})
    except ErroDeValidacao as erro:
        return jsonify({"erro": str(erro)}), 400
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify(jogo.to_dict())


@api_jogos_bp.route("/<int:jogo_id>", methods=["DELETE"])
@api_login_required
def excluir(jogo_id):
    servico = BacklogService(usuario_atual())
    try:
        servico.excluir_jogo(jogo_id)
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return "", 204
