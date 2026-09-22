from flask import Blueprint, jsonify, request

from app.services.backlog_service import BacklogService, ErroDeValidacao, RecursoNaoEncontrado
from app.utils.auth import api_login_required, usuario_atual

api_runs_bp = Blueprint("api_runs", __name__, url_prefix="/api/runs")


def _dados_json():
    dados = request.get_json(silent=True)
    return {} if dados is None else dados


@api_runs_bp.route("", methods=["GET"])
@api_login_required
def listar():
    servico = BacklogService(usuario_atual())
    return jsonify([run.to_dict() for run in servico.listar_runs()])


@api_runs_bp.route("/<int:run_id>", methods=["GET"])
@api_login_required
def obter(run_id):
    servico = BacklogService(usuario_atual())
    try:
        run = servico.obter_run(run_id)
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify(run.to_dict())


@api_runs_bp.route("", methods=["POST"])
@api_login_required
def criar():
    servico = BacklogService(usuario_atual())
    try:
        run = servico.registrar_run(_dados_json())
    except ErroDeValidacao as erro:
        return jsonify({"erro": str(erro)}), 400
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify(run.to_dict()), 201


@api_runs_bp.route("/<int:run_id>", methods=["PUT"])
@api_login_required
def atualizar(run_id):
    servico = BacklogService(usuario_atual())
    try:
        run = servico.atualizar_run(run_id, _dados_json())
    except ErroDeValidacao as erro:
        return jsonify({"erro": str(erro)}), 400
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify(run.to_dict())


@api_runs_bp.route("/<int:run_id>", methods=["DELETE"])
@api_login_required
def excluir(run_id):
    servico = BacklogService(usuario_atual())
    try:
        servico.excluir_run(run_id)
    except RecursoNaoEncontrado as erro:
        return jsonify({"erro": str(erro)}), 404
    return "", 204
