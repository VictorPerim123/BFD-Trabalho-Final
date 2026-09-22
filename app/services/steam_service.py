from concurrent.futures import ThreadPoolExecutor

import requests

BASE_URL = "https://api.steampowered.com"
STORE_API_URL = "https://store.steampowered.com/api/appdetails"
TIMEOUT_SEGUNDOS = 6
MAX_WORKERS = 6


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

    def obter_biblioteca(self, steamid64):

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

        jogos = [self._normalizar_jogo(jogo) for jogo in payload["games"]]
        if not jogos:
            return []

        workers = min(MAX_WORKERS, len(jogos))
        if workers == 1:
            return [self._enriquecer_jogo(jogos[0], steamid64)]

        with ThreadPoolExecutor(max_workers=workers) as executor:
            return list(executor.map(lambda jogo: self._enriquecer_jogo(jogo, steamid64), jogos))

    @staticmethod
    def _normalizar_jogo(jogo):
        appid = jogo["appid"]
        return {
            "steam_appid": appid,
            "titulo": jogo.get("name", f"Jogo Steam #{appid}"),
            "tempo_jogado_horas": (jogo.get("playtime_forever", 0) + 30) // 60,
        }

    def _enriquecer_jogo(self, jogo, steamid64):
        item = dict(jogo)
        appid = item["steam_appid"]

        item["capa_url"] = self._obter_capa(appid)

        conquistas = self._obter_conquistas(steamid64, appid)
        if conquistas is None:
            item["total_conquistas"] = 0
            item["conquistas_obtidas"] = 0
            item["conquistas_sincronizadas"] = False
        else:
            total, obtidas = conquistas
            item["total_conquistas"] = total
            item["conquistas_obtidas"] = obtidas
            item["conquistas_sincronizadas"] = True

        return item

    def _obter_conquistas(self, steamid64, appid):
        try:
            resp = requests.get(
                f"{BASE_URL}/ISteamUserStats/GetPlayerAchievements/v1/",
                params={
                    "key": self.api_key,
                    "steamid": steamid64,
                    "appid": appid,
                    "l": "brazilian",
                    "format": "json",
                },
                timeout=TIMEOUT_SEGUNDOS,
            )
            resp.raise_for_status()
            playerstats = resp.json().get("playerstats", {})
        except (requests.RequestException, ValueError):
            return None

        if playerstats.get("success") is False:
            erro = str(playerstats.get("error", "")).casefold()
            if "no stats" in erro or "no achievements" in erro:
                return (0, 0)
            return None

        conquistas = playerstats.get("achievements")
        if conquistas is None:
            return None
        if not isinstance(conquistas, list):
            return None

        total = len(conquistas)
        obtidas = sum(1 for conquista in conquistas if conquista.get("achieved") == 1)
        return total, obtidas

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
