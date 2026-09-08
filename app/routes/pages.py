from flask import Blueprint, render_template

from app.utils.auth import login_required

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
@login_required
def raiz():
    return render_template("inicio.html")
