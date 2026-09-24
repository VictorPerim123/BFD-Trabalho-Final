from app.services.backlog_service import BacklogService
from app.services.steam_service import SteamService


class SteamSyncService:
    def __init__(self, usuario, api_key):
        self.usuario = usuario
        self.steam = SteamService(api_key)
        self.backlog = BacklogService(usuario)

    def previsualizar(
        self,
        identificador,
        *,
        classificar_status=False,
        reclassificar_existentes=False,
    ):
        steamid = self.steam.resolver_steamid(identificador)
        biblioteca = self.steam.obter_biblioteca(
            steamid,
            incluir_atividade_recente=classificar_status,
            incluir_capas=False,
            incluir_detalhes_conquistas=False,
        )
        resultado = self.backlog.prever_importacao_steam(
            biblioteca,
            classificar_status=classificar_status,
            reclassificar_existentes=reclassificar_existentes,
        )
        resultado["encontrados"] = len(biblioteca)
        resultado["steam_id"] = steamid
        return resultado

    def sincronizar(
        self,
        identificador,
        *,
        classificar_status=False,
        reclassificar_existentes=False,
    ):
        steamid = self.steam.resolver_steamid(identificador)
        biblioteca = self.steam.obter_biblioteca(
            steamid,
            incluir_atividade_recente=classificar_status,
        )
        self.usuario.steam_id = steamid
        resultado = self.backlog.importar_jogos_steam(
            biblioteca,
            classificar_status=classificar_status,
            reclassificar_existentes=reclassificar_existentes,
        )
        resultado["encontrados"] = len(biblioteca)
        resultado["steam_id"] = steamid
        return resultado
