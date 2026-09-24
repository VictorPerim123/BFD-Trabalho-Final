from concurrent.futures import ThreadPoolExecutor
import logging
import time

import requests

BASE_URL = "https://api.steampowered.com"
STORE_API_URL = "https://store.steampowered.com/api/appdetails"
TIMEOUT_SEGUNDOS = 10
MAX_WORKERS_CONQUISTAS = 2
MAX_WORKERS_CAPAS = 4
MAX_TENTATIVAS = 3
STATUS_REPETIR = {429, 500, 502, 503, 504}

logger = logging.getLogger(__name__)


class SteamNaoConfigurado(Exception):
    pass


class SteamErroDeComunicacao(Exception):
    pass


class SteamPerfilIndisponivel(Exception):
    pass


class SteamService:
    def __init__(self, api_key):
        if not api_key:
            raise SteamNaoConfigurado(
                "STEAM_API_KEY não configurada. Gere uma chave gratuita em "
                "https://steamcommunity.com/dev/apikey e defina no arquivo .env."
            )
        self.api_key = api_key

    def resolver_steamid(self, entrada):
        entrada = (entrada or "").strip()
        if not entrada:
            raise SteamPerfilIndisponivel("Informe um SteamID64 ou vanity URL.")

        limpa = entrada.split("?", 1)[0].split("#", 1)[0].rstrip("/")
        ultimo_segmento = limpa.split("/")[-1]
        if ultimo_segmento.isdigit() and len(ultimo_segmento) == 17:
            return ultimo_segmento

        vanity = ultimo_segmento
        if not vanity:
            raise SteamPerfilIndisponivel("Informe um SteamID64 ou vanity URL.")

        try:
            resp = requests.get(
                f"{BASE_URL}/ISteamUser/ResolveVanityURL/v1/",
                params={"key": self.api_key, "vanityurl": vanity},
                timeout=TIMEOUT_SEGUNDOS,
            )
            resp.raise_for_status()
            payload = resp.json().get("response", {})
        except (requests.RequestException, ValueError) as exc:
            raise SteamErroDeComunicacao(f"Falha ao conectar à Steam: {exc}") from exc

        if payload.get("success") != 1:
            raise SteamPerfilIndisponivel(
                "Não foi possível resolver esse usuário Steam. Verifique o SteamID/vanity URL."
            )
        return payload["steamid"]

    def obter_biblioteca(
        self,
        steamid64,
        incluir_atividade_recente=False,
        *,
        incluir_capas=True,
        incluir_detalhes_conquistas=True,
    ):
        try:
            resp = requests.get(
                f"{BASE_URL}/IPlayerService/GetOwnedGames/v1/",
                params={
                    "key": self.api_key,
                    "steamid": steamid64,
                    "include_appinfo": 1,
                    "include_played_free_games": 1,
                    "format": "json",
                },
                timeout=TIMEOUT_SEGUNDOS,
            )
            resp.raise_for_status()
            payload = resp.json().get("response", {})
        except (requests.RequestException, ValueError) as exc:
            raise SteamErroDeComunicacao(f"Falha ao conectar à Steam: {exc}") from exc

        if "games" not in payload:
            raise SteamPerfilIndisponivel(
                "Biblioteca de jogos indisponível — o perfil Steam pode estar privado. "
                "Ative 'Detalhes do jogo' como público em Configurações da Steam > Privacidade."
            )

        recentes = self._obter_jogos_recentes(steamid64) if incluir_atividade_recente else None
        jogos = [self._normalizar_jogo(jogo, recentes) for jogo in payload["games"]]
        if not jogos:
            return []

        self._sincronizar_conquistas(
            jogos,
            steamid64,
            incluir_detalhes=incluir_detalhes_conquistas,
        )
        if incluir_capas:
            self._sincronizar_capas(jogos)
        return jogos

    @staticmethod
    def _normalizar_jogo(jogo, recentes=None):
        appid = jogo["appid"]
        minutos = max(0, int(jogo.get("playtime_forever", 0) or 0))
        return {
            "steam_appid": appid,
            "titulo": jogo.get("name", f"Jogo Steam #{appid}"),
            "tempo_jogado_horas": (minutos + 30) // 60,
            "tempo_jogado_minutos": minutos,
            "atividade_recente": appid in recentes if recentes is not None else False,
            "atividade_recente_disponivel": recentes is not None,
        }

    def _obter_jogos_recentes(self, steamid64):
        try:
            resp = requests.get(
                f"{BASE_URL}/IPlayerService/GetRecentlyPlayedGames/v1/",
                params={
                    "key": self.api_key,
                    "steamid": steamid64,
                    "count": 0,
                    "format": "json",
                },
                timeout=TIMEOUT_SEGUNDOS,
            )
            resp.raise_for_status()
            payload = resp.json().get("response", {})
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Falha ao consultar jogos recentes da Steam: %s", exc)
            return None

        games = payload.get("games", [])
        if not isinstance(games, list):
            return None
        return {
            game.get("appid")
            for game in games
            if isinstance(game, dict) and game.get("appid") is not None
        }

    def _sincronizar_conquistas(self, jogos, steamid64, *, incluir_detalhes=True):
        workers = min(MAX_WORKERS_CONQUISTAS, len(jogos))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            resultados = list(
                executor.map(
                    lambda jogo: self._obter_conquistas(
                        steamid64,
                        jogo["steam_appid"],
                        incluir_detalhes=incluir_detalhes,
                    ),
                    jogos,
                )
            )

        for jogo, resultado in zip(jogos, resultados):
            if resultado is None:
                jogo["total_conquistas"] = 0
                jogo["conquistas_obtidas"] = 0
                jogo["conquistas_sincronizadas"] = False
                jogo["conquistas_disponiveis"] = False
                jogo["conquistas_detalhes"] = []
                continue

            total, obtidas, disponiveis, detalhes = resultado
            jogo["total_conquistas"] = total
            jogo["conquistas_obtidas"] = obtidas
            jogo["conquistas_sincronizadas"] = True
            jogo["conquistas_disponiveis"] = disponiveis
            jogo["conquistas_detalhes"] = detalhes

    def _sincronizar_capas(self, jogos):
        workers = min(MAX_WORKERS_CAPAS, len(jogos))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            capas = list(executor.map(lambda jogo: self._obter_capa(jogo["steam_appid"]), jogos))

        for jogo, capa in zip(jogos, capas):
            jogo["capa_url"] = capa

    def _obter_conquistas(self, steamid64, appid, *, incluir_detalhes=True):
        url = f"{BASE_URL}/ISteamUserStats/GetPlayerAchievements/v1/"
        params = {
            "key": self.api_key,
            "steamid": steamid64,
            "appid": appid,
            "l": "brazilian",
            "format": "json",
        }

        for tentativa in range(MAX_TENTATIVAS):
            try:
                resp = requests.get(url, params=params, timeout=TIMEOUT_SEGUNDOS)
            except requests.RequestException as exc:
                if tentativa + 1 < MAX_TENTATIVAS:
                    time.sleep(0.5 * (tentativa + 1))
                    continue
                logger.warning("Falha ao consultar conquistas do AppID %s: %s", appid, exc)
                return None

            try:
                payload = resp.json()
            except ValueError as exc:
                status = getattr(resp, "status_code", 200)
                if status in STATUS_REPETIR and tentativa + 1 < MAX_TENTATIVAS:
                    time.sleep(0.5 * (tentativa + 1))
                    continue
                logger.warning(
                    "Resposta inválida ao consultar conquistas do AppID %s: HTTP %s, %s",
                    appid,
                    status,
                    exc,
                )
                return None

            playerstats = payload.get("playerstats", {}) if isinstance(payload, dict) else {}
            erro = str(playerstats.get("error", ""))
            erro_normalizado = erro.casefold()

            if playerstats.get("success") is False and (
                "no stats" in erro_normalizado or "no achievements" in erro_normalizado
            ):
                return 0, 0, False, []

            status = getattr(resp, "status_code", 200)
            if status in STATUS_REPETIR and tentativa + 1 < MAX_TENTATIVAS:
                time.sleep(0.5 * (tentativa + 1))
                continue

            if status >= 400:
                logger.warning(
                    "Steam retornou HTTP %s para conquistas do AppID %s: %s",
                    status,
                    appid,
                    erro or "sem detalhe",
                )
                return None

            if playerstats.get("success") is False:
                logger.warning(
                    "Steam não disponibilizou conquistas do AppID %s: %s",
                    appid,
                    erro or "sem detalhe",
                )
                return None

            conquistas = playerstats.get("achievements")
            if conquistas is None:
                logger.warning("Steam não retornou o campo achievements para o AppID %s", appid)
                return None
            if not isinstance(conquistas, list):
                logger.warning("Steam retornou achievements inválido para o AppID %s", appid)
                return None

            total = len(conquistas)
            obtidas = sum(1 for conquista in conquistas if self._conquista_obtida(conquista))
            if not incluir_detalhes:
                return total, obtidas, True, []

            schema = self._obter_schema_conquistas(appid)
            detalhes = []
            for conquista in conquistas:
                if not isinstance(conquista, dict):
                    continue
                api_name = str(conquista.get("apiname") or "").strip()
                if not api_name:
                    continue
                metadados = schema.get(api_name, {})
                nome = (
                    metadados.get("displayName")
                    or conquista.get("name")
                    or api_name
                )
                descricao = metadados.get("description") or conquista.get("description")
                detalhes.append(
                    {
                        "api_name": api_name,
                        "nome": str(nome).strip(),
                        "descricao": str(descricao).strip() if descricao else None,
                        "icone_url": self._url_https(metadados.get("icon") or conquista.get("icon")),
                        "icone_bloqueada_url": self._url_https(
                            metadados.get("icongray") or conquista.get("icongray")
                        ),
                        "desbloqueada": self._conquista_obtida(conquista),
                        "unlocktime": conquista.get("unlocktime"),
                    }
                )
            return total, obtidas, True, detalhes

        return None

    def _obter_schema_conquistas(self, appid):
        url = f"{BASE_URL}/ISteamUserStats/GetSchemaForGame/v2/"
        params = {
            "key": self.api_key,
            "appid": appid,
            "l": "brazilian",
            "format": "json",
        }

        for tentativa in range(MAX_TENTATIVAS):
            try:
                resp = requests.get(url, params=params, timeout=TIMEOUT_SEGUNDOS)
                status = getattr(resp, "status_code", 200)
                if status in STATUS_REPETIR and tentativa + 1 < MAX_TENTATIVAS:
                    time.sleep(0.5 * (tentativa + 1))
                    continue
                if status >= 400:
                    return {}
                payload = resp.json()
            except (requests.RequestException, ValueError) as exc:
                if tentativa + 1 < MAX_TENTATIVAS:
                    time.sleep(0.5 * (tentativa + 1))
                    continue
                logger.warning("Falha ao consultar schema de conquistas do AppID %s: %s", appid, exc)
                return {}

            game = payload.get("game", {}) if isinstance(payload, dict) else {}
            stats = game.get("availableGameStats", {}) if isinstance(game, dict) else {}
            achievements = stats.get("achievements", []) if isinstance(stats, dict) else []
            if not isinstance(achievements, list):
                return {}
            return {
                str(item.get("name")): item
                for item in achievements
                if isinstance(item, dict) and item.get("name")
            }

        return {}

    @staticmethod
    def _url_https(valor):
        if not isinstance(valor, str):
            return None
        url = valor.strip()
        return url if url.startswith("https://") else None

    @staticmethod
    def _conquista_obtida(conquista):
        if not isinstance(conquista, dict):
            return False
        valor = conquista.get("achieved")
        if valor is True or valor == 1:
            return True
        if isinstance(valor, str):
            return valor.strip().casefold() in {"1", "true"}
        return False

    def _obter_capa(self, appid):
        fallback = f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"
        try:
            resp = requests.get(
                STORE_API_URL,
                params={"appids": appid, "l": "brazilian", "cc": "br"},
                timeout=TIMEOUT_SEGUNDOS,
            )
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError):
            return fallback

        app = payload.get(str(appid), {}) if isinstance(payload, dict) else {}
        dados = app.get("data", {}) if app.get("success") else {}
        return (
            dados.get("header_image")
            or dados.get("capsule_image")
            or dados.get("capsule_imagev5")
            or fallback
        )
