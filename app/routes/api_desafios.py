from flask import Blueprint, jsonify, request

from app.services.backlog_service import BacklogService, ErroDeValidacao, RecursoNaoEncontrado
from app.utils.auth import api_login_required, usuario_atual

api_desafios_bp = Blueprint("api_desafios", __name__, url_prefix="/api/desafios")


def _dados_json():
    dados = request.get_json(silent=True)
    return {} if dados is None else dados


@api_desafios_bp.route("", methods=["GET"])
@api_login_required
def listar():
    servico = BacklogService(usuario_atual())
    return jsonify([desafio.to_dict() for desafio in servico.listar_desafios()])


@api_desafios_bp.route("/<int:desafio_id>", methods=["GET"])
@api_login_required
def obter(desafio_id):
    servico = BacklogService(usuario_atual())
    try:
        desafio = servico.obter_desafio(desafio_id)
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify(desafio.to_dict())


@api_desafios_bp.route("", methods=["POST"])
@api_login_required
def criar():
    servico = BacklogService(usuario_atual())
    try:
        desafio = servico.registrar_desafio(_dados_json())
    except ErroDeValidacao as erro:
        return jsonify({"erro": str(erro)}), 400
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify(desafio.to_dict()), 201


@api_desafios_bp.route("/<int:desafio_id>", methods=["PUT"])
@api_login_required
def atualizar(desafio_id):
    servico = BacklogService(usuario_atual())
    try:
        desafio = servico.atualizar_desafio(desafio_id, _dados_json())
    except ErroDeValidacao as erro:
        return jsonify({"erro": str(erro)}), 400
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify(desafio.to_dict())


@api_desafios_bp.route("/<int:desafio_id>", methods=["DELETE"])
@api_login_required
def excluir(desafio_id):
    servico = BacklogService(usuario_atual())
    try:
        servico.excluir_desafio(desafio_id)
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return "", 204
