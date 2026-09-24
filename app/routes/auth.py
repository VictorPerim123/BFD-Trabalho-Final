import re
from urllib.parse import urlsplit

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.extensions import db
from app.models import Usuario
from app.utils.auth import login_required, usuario_atual, SESSION_KEY

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
            try:
                partes = urlsplit(destino)
            except ValueError:
                destino = url_for("pages.raiz")
            else:
                if (
                    partes.scheme
                    or partes.netloc
                    or not destino.startswith("/")
                    or destino.startswith(("//", "/\\"))
                ):
                    destino = url_for("pages.raiz")
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
        elif len(nome) > 120:
            erro = "O nome deve ter no máximo 120 caracteres."
        elif len(username) > 60:
            erro = "O usuário deve ter no máximo 60 caracteres."
        elif len(email) > 160:
            erro = "O e-mail deve ter no máximo 160 caracteres."
        elif not EMAIL_RE.fullmatch(email):
            erro = "Informe um e-mail válido."
        elif len(senha) < 8:
            erro = "A senha deve ter ao menos 8 caracteres."
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


@auth_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    usuario = usuario_atual()
    erro_dados = None
    erro_senha = None
    dados = {
        "nome": usuario.nome or "",
        "username": usuario.username or "",
        "email": usuario.email or "",
        "steam_id": usuario.steam_id or "",
    }

    if request.method == "POST":
        acao = request.form.get("acao")
        if acao == "dados":
            dados = {
                "nome": (request.form.get("nome") or "").strip(),
                "username": (request.form.get("username") or "").strip(),
                "email": (request.form.get("email") or "").strip(),
                "steam_id": (request.form.get("steam_id") or "").strip(),
            }
            steam_id = dados["steam_id"] or None

            if not dados["nome"] or not dados["username"] or not dados["email"]:
                erro_dados = "Preencha nome, usuário e e-mail."
            elif len(dados["nome"]) > 120:
                erro_dados = "O nome deve ter no máximo 120 caracteres."
            elif len(dados["username"]) > 60:
                erro_dados = "O usuário deve ter no máximo 60 caracteres."
            elif len(dados["email"]) > 160:
                erro_dados = "O e-mail deve ter no máximo 160 caracteres."
            elif not EMAIL_RE.fullmatch(dados["email"]):
                erro_dados = "Informe um e-mail válido."
            elif steam_id and len(steam_id) > 32:
                erro_dados = "O SteamID ou vanity deve ter no máximo 32 caracteres."
            else:
                duplicado = Usuario.query.filter(
                    Usuario.id != usuario.id,
                    (Usuario.username == dados["username"]) | (Usuario.email == dados["email"]),
                ).first()
                if duplicado:
                    erro_dados = "Já existe uma conta com esse usuário ou e-mail."
                else:
                    usuario.nome = dados["nome"]
                    usuario.username = dados["username"]
                    usuario.email = dados["email"]
                    usuario.steam_id = steam_id
                    db.session.commit()
                    flash("Perfil atualizado com sucesso.")
                    return redirect(url_for("auth.perfil"))

        elif acao == "senha":
            senha_atual = request.form.get("senha_atual") or ""
            nova_senha = request.form.get("nova_senha") or ""
            confirmar_senha = request.form.get("confirmar_senha") or ""

            if not usuario.verificar_senha(senha_atual):
                erro_senha = "A senha atual está incorreta."
            elif len(nova_senha) < 8:
                erro_senha = "A nova senha deve ter ao menos 8 caracteres."
            elif nova_senha != confirmar_senha:
                erro_senha = "A confirmação da nova senha não confere."
            else:
                usuario.set_senha(nova_senha)
                db.session.commit()
                flash("Senha atualizada com sucesso.")
                return redirect(url_for("auth.perfil"))
        else:
            erro_dados = "Ação de perfil inválida."

    criado_em = usuario.criado_em
    if hasattr(criado_em, "strftime"):
        criado_em_formatado = criado_em.strftime("%d/%m/%Y")
    elif criado_em:
        criado_em_formatado = str(criado_em).split(" ", 1)[0]
    else:
        criado_em_formatado = "—"

    return render_template(
        "perfil.html",
        usuario=usuario,
        dados=dados,
        criado_em_formatado=criado_em_formatado,
        erro_dados=erro_dados,
        erro_senha=erro_senha,
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.")
    return redirect(url_for("auth.login"))
