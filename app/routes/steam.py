from flask import Blueprint, current_app, render_template, request

from app.services.backlog_service import BacklogService, ErroDeValidacao
from app.services.steam_service import (
    SteamService,
    SteamNaoConfigurado,
    SteamErroDeComunicacao,
    SteamPerfilIndisponivel,
)
from app.utils.auth import login_required, usuario_atual

steam_bp = Blueprint("steam", __name__, url_prefix="/steam")


@steam_bp.route("/importar", methods=["GET", "POST"])
@login_required
def importar():
    erro = None
    resultado = None

    if request.method == "POST":
        identificador = request.form.get("identificador", "")
        try:
            servico_steam = SteamService(current_app.config.get("STEAM_API_KEY"))
            steamid = servico_steam.resolver_steamid(identificador)
            biblioteca = servico_steam.obter_biblioteca(steamid)
            resultado = BacklogService(usuario_atual()).importar_jogos_steam(biblioteca)
        except SteamNaoConfigurado as exc:
            erro = str(exc)
        except (SteamErroDeComunicacao, SteamPerfilIndisponivel, ErroDeValidacao) as exc:
            erro = str(exc)

    return render_template("steam_importar.html", erro=erro, resultado=resultado)
