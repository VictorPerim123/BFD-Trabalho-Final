"""
routes/steam.py — importação opcional da biblioteca Steam (integração
externa, requisito 2.3). Complementa o cadastro manual: cria jogos que
ainda não existem e sincroniza tempo jogado e contadores de conquistas dos
já importados, usando steam_appid como identificador estável.
"""

from flask import Blueprint, render_template, request, current_app

from app.extensions import db
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
            jogos_existentes = {
                jogo.steam_appid: jogo
                for jogo in usuario.jogos.all()
                if jogo.steam_appid is not None
            }

            servico_backlog = BacklogService(usuario)
            importados = 0
            atualizados = 0
            conquistas_sincronizadas = 0
            conquistas_indisponiveis = 0

            for jogo_steam in biblioteca:
                appid = jogo_steam["steam_appid"]
                jogo_existente = jogos_existentes.get(appid)

                # Conquistas são consultadas por AppID. Falta de suporte ou
                # privacidade não impede a importação do restante da biblioteca.
                contadores_conquistas = servico_steam.obter_conquistas(steamid, appid)
                if contadores_conquistas is None:
                    conquistas_indisponiveis += 1
                else:
                    conquistas_sincronizadas += 1

                if jogo_existente is not None:
                    # A Steam é fonte de tempo e contadores de conquistas.
                    # Dados pessoais como status, nota, categorias, runs e builds
                    # continuam sendo preservados.
                    jogo_existente.tempo_jogado_horas = jogo_steam["tempo_jogado_horas"]
                    if contadores_conquistas is not None:
                        jogo_existente.total_conquistas = contadores_conquistas["total_conquistas"]
                        jogo_existente.conquistas_obtidas = contadores_conquistas["conquistas_obtidas"]
                    atualizados += 1
                    continue

                dados_novo_jogo = {
                    "titulo": jogo_steam["titulo"],
                    "status": "quero_jogar",
                    "tempo_jogado_horas": jogo_steam["tempo_jogado_horas"],
                    "steam_appid": appid,
                }
                if contadores_conquistas is not None:
                    dados_novo_jogo.update(contadores_conquistas)

                novo_jogo = servico_backlog.criar_jogo(dados_novo_jogo)
                jogos_existentes[appid] = novo_jogo
                importados += 1

            # criar_jogo já persiste os novos registros; este commit grava
            # as sincronizações dos jogos que já estavam no backlog.
            db.session.commit()

            resultado = {
                "importados": importados,
                "atualizados": atualizados,
                "conquistas_sincronizadas": conquistas_sincronizadas,
                "conquistas_indisponiveis": conquistas_indisponiveis,
                "total": len(biblioteca),
            }
        except SteamNaoConfigurado as exc:
            erro = str(exc)
        except (SteamErroDeComunicacao, SteamPerfilIndisponivel) as exc:
            erro = str(exc)

    return render_template("steam_importar.html", erro=erro, resultado=resultado)
