import requests

BASE_URL = "https://api.steampowered.com"
TIMEOUT_SEGUNDOS = 6


class SteamNaoConfigurado(Exception):
    """"""


class SteamErroDeComunicacao(Exception):
    """"""


class SteamPerfilIndisponivel(Exception):
    """"""


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
        if entrada.isdigit() and len(entrada) == 17:
            return entrada

        vanity = entrada.rstrip("/").split("/")[-1]

        try:
            resp = requests.get(
                f"{BASE_URL}/ISteamUser/ResolveVanityURL/v1/",
                params={"key": self.api_key, "vanityurl": vanity},
                timeout=TIMEOUT_SEGUNDOS,
            )
            resp.raise_for_status()
            payload = resp.json().get("response", {})
        except requests.RequestException as exc:
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
        except requests.RequestException as exc:
            raise SteamErroDeComunicacao(f"Falha ao conectar à Steam: {exc}") from exc

        if "games" not in payload:
            raise SteamPerfilIndisponivel(
                "Biblioteca de jogos indisponível — o perfil Steam pode estar privado. "
                "Ative 'Detalhes do jogo' como público em Configurações da Steam > Privacidade."
            )

        return [
            {
                "steam_appid": jogo["appid"],
                "titulo": jogo.get("name", f"Jogo Steam #{jogo['appid']}"),
                "tempo_jogado_horas": (jogo.get("playtime_forever", 0) + 30) // 60,
            }
            for jogo in payload["games"]
        ]
