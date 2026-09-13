from flask import Blueprint, render_template, request, current_app

from app.services.backlog_service import BacklogService
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

            usuario = usuario_atual()
            appids_existentes = {
                j.steam_appid for j in usuario.jogos if j.steam_appid is not None
            }

            servico_backlog = BacklogService(usuario)
            importados = 0
            for jogo_steam in biblioteca:
                if jogo_steam["steam_appid"] in appids_existentes:
                    continue
                servico_backlog.criar_jogo(
                    {
                        "titulo": jogo_steam["titulo"],
                        "status": "quero_jogar",
                        "tempo_jogado_horas": jogo_steam["tempo_jogado_horas"],
                        "steam_appid": jogo_steam["steam_appid"],
                    }
                )
                importados += 1

            resultado = {
                "importados": importados,
                "ignorados": len(biblioteca) - importados,
            }
        except SteamNaoConfigurado as exc:
            erro = str(exc)
        except (SteamErroDeComunicacao, SteamPerfilIndisponivel) as exc:
            erro = str(exc)

    return render_template("steam_importar.html", erro=erro, resultado=resultado)
