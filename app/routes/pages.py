
from flask import Blueprint, render_template, redirect, url_for

from app.utils.auth import login_required

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def raiz():
    return redirect(url_for("pages.backlog"))


@pages_bp.route("/backlog")
@login_required
def backlog():
    return render_template("backlog.html")


@pages_bp.route("/runs/novo")
@login_required
def run_form():
    return render_template("run-form.html")


@pages_bp.route("/runs")
@login_required
def runs():
    return render_template("runs.html")


@pages_bp.route("/builds")
@login_required
def builds():
    return render_template("builds.html")
