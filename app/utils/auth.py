from functools import wraps

from flask import session, redirect, url_for, request, jsonify

from app.extensions import db
from app.models import Usuario

SESSION_KEY = "usuario_id"


def usuario_atual():
    usuario_id = session.get(SESSION_KEY)
    if usuario_id is None:
        return None
    return db.session.get(Usuario, usuario_id)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if usuario_atual() is None:
            return redirect(url_for("auth.login", proximo=request.path))
        return view_func(*args, **kwargs)

    return wrapper


def api_login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if usuario_atual() is None:
            return jsonify({"erro": "Autenticação necessária."}), 401
        return view_func(*args, **kwargs)

    return wrapper
