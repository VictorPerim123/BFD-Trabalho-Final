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
