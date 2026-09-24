from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.services.backlog_service import BacklogService, RecursoNaoEncontrado
from app.utils.auth import login_required, usuario_atual

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def raiz():
    return redirect(url_for("pages.dashboard"))


@pages_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@pages_bp.route("/backlog")
@login_required
def backlog():
    return render_template("backlog.html")


@pages_bp.route("/jogos/<int:jogo_id>")
@login_required
def jogo_detalhe(jogo_id):
    try:
        jornada = BacklogService(usuario_atual()).obter_jornada_jogo(jogo_id)
    except RecursoNaoEncontrado:
        abort(404)
    return render_template("jogo-detalhe.html", **jornada)


@pages_bp.route("/jornada")
@login_required
def jornada():
    return render_template("jornada.html")


@pages_bp.route("/runs/novo")
@login_required
def run_form():
    parametros = {"aba": "runs", "acao": "nova-run"}
    jogo_id = request.args.get("jogo_id", type=int)
    run_id = request.args.get("run_id", type=int)
    if jogo_id:
        parametros["jogo_id"] = jogo_id
    if run_id:
        parametros["run_id"] = run_id
        parametros["acao"] = "editar-run"
    return redirect(url_for("pages.jornada", **parametros))


@pages_bp.route("/runs")
@login_required
def runs():
    return redirect(url_for("pages.jornada", aba="runs"))


@pages_bp.route("/builds")
@login_required
def builds():
    return redirect(url_for("pages.jornada", aba="builds"))


@pages_bp.route("/desafios")
@login_required
def desafios():
    return render_template("desafios.html")
