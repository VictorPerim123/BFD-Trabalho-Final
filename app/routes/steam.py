from flask import Blueprint, current_app, render_template, request

from app.services.backlog_service import ErroDeValidacao
from app.services.steam_service import SteamErroDeComunicacao, SteamNaoConfigurado, SteamPerfilIndisponivel
from app.services.steam_sync_service import SteamSyncService
from app.utils.auth import login_required, usuario_atual

steam_bp = Blueprint("steam", __name__, url_prefix="/steam")


@steam_bp.route("/importar", methods=["GET", "POST"])
@login_required
def importar():
    erro = None
    resultado = None
    previsao = None
    modo_modal = request.args.get("modal") == "1" or request.form.get("modo_modal") == "1"
    identificador = getattr(usuario_atual(), "steam_id", "") or ""
    classificacao_status = "automatico"
    reclassificar_existentes = False

    if request.method == "POST":
        identificador = request.form.get("identificador", "")
        classificacao_status = request.form.get("classificacao_status", "manter")
        reclassificar_existentes = request.form.get("reclassificar_existentes") == "1"
        classificar_status = classificacao_status == "automatico"
        acao = request.form.get("acao", "previsualizar")
        try:
            if classificacao_status not in {"automatico", "manter"}:
                raise ErroDeValidacao("Opção de classificação de status inválida.")
            if acao not in {"previsualizar", "sincronizar"}:
                raise ErroDeValidacao("Ação de importação inválida.")
            servico = SteamSyncService(
                usuario_atual(), current_app.config.get("STEAM_API_KEY")
            )
            if acao == "sincronizar":
                resultado = servico.sincronizar(
                    identificador,
                    classificar_status=classificar_status,
                    reclassificar_existentes=reclassificar_existentes,
                )
            else:
                previsao = servico.previsualizar(
                    identificador,
                    classificar_status=classificar_status,
                    reclassificar_existentes=reclassificar_existentes,
                )
        except SteamNaoConfigurado as exc:
            erro = str(exc)
        except (SteamErroDeComunicacao, SteamPerfilIndisponivel, ErroDeValidacao) as exc:
            erro = str(exc)

    template = "_steam_import_content.html" if modo_modal else "steam_importar.html"
    return render_template(
        template,
        erro=erro,
        resultado=resultado,
        previsao=previsao,
        identificador=identificador,
        classificacao_status=classificacao_status,
        reclassificar_existentes=reclassificar_existentes,
        modo_modal=modo_modal,
    )
