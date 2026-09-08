"""
routes/auth.py — cadastro, login e logout (sessão + senha com hash).
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.extensions import db
from app.models import Usuario
from app.utils.auth import usuario_atual, SESSION_KEY

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if usuario_atual() is not None:
        return redirect(url_for("pages.raiz"))

    erro = None
    if request.method == "POST":
        identificador = (request.form.get("usuario") or "").strip()
        senha = request.form.get("senha") or ""

        usuario = Usuario.query.filter(
            (Usuario.username == identificador) | (Usuario.email == identificador)
        ).first()

        if usuario is not None and usuario.verificar_senha(senha):
            session.clear()
            session[SESSION_KEY] = usuario.id
            session.permanent = True
            destino = request.args.get("proximo") or url_for("pages.raiz")
            return redirect(destino)

        erro = "Usuário/e-mail ou senha inválidos."

    return render_template("login.html", erro=erro)


@auth_bp.route("/registrar", methods=["GET", "POST"])
def registrar():
    if usuario_atual() is not None:
        return redirect(url_for("pages.raiz"))

    erro = None
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        senha = request.form.get("senha") or ""

        if not nome or not username or not email or not senha:
            erro = "Preencha todos os campos."
        elif len(senha) < 6:
            erro = "A senha deve ter ao menos 6 caracteres."
        elif Usuario.query.filter(
            (Usuario.username == username) | (Usuario.email == email)
        ).first():
            erro = "Já existe uma conta com esse usuário ou e-mail."
        else:
            usuario = Usuario(nome=nome, username=username, email=email)
            usuario.set_senha(senha)
            db.session.add(usuario)
            db.session.commit()

            session.clear()
            session[SESSION_KEY] = usuario.id
            session.permanent = True
            return redirect(url_for("pages.raiz"))

    return render_template("registrar.html", erro=erro)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.")
    return redirect(url_for("auth.login"))
