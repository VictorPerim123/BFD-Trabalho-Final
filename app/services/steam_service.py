"""
SteamService — integração externa opcional com a Steam Web API.

Conforme discutido no planejamento: a importação da Steam é um
COMPLEMENTO ao cadastro manual, nunca um substituto — ela preenche
título/tempo jogado ao importar jogos novos e permite sincronizar tempo e
contadores de conquistas dos jogos já importados; status, nota, categorias
e demais dados pessoais continuam sendo decisão do jogador.

Documentação oficial: https://developer.valvesoftware.com/wiki/Steam_Web_API
"""

import requests

BASE_URL = "https://api.steampowered.com"
TIMEOUT_SEGUNDOS = 6


class SteamNaoConfigurado(Exception):
    """STEAM_API_KEY não foi definida no ambiente."""


class SteamErroDeComunicacao(Exception):
    """Falha de rede, timeout ou resposta inesperada da Steam."""


class SteamPerfilIndisponivel(Exception):
    """SteamID inválido/inexistente ou perfil com biblioteca de jogos privada."""


class SteamService:
    def __init__(self, api_key):
        if not api_key:
            raise SteamNaoConfigurado(
                "STEAM_API_KEY não configurada. Gere uma chave gratuita em "
                "https://steamcommunity.com/dev/apikey e defina no arquivo .env."
            )
        self.api_key = api_key

    def resolver_steamid(self, entrada):
        """Aceita um SteamID64 (17 dígitos) ou uma vanity URL (steamcommunity.com/id/<nome>)
        e retorna sempre o SteamID64 numérico."""
        entrada = (entrada or "").strip()
        if entrada.isdigit() and len(entrada) == 17:
            return entrada

        # extrai o último segmento caso o usuário cole a URL completa
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
        """Retorna [{appid, nome, tempo_jogado_horas}, ...] da biblioteca pública do usuário."""
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
                "tempo_jogado_horas": round(jogo.get("playtime_forever", 0) / 60),
            }
            for jogo in payload["games"]
        ]

    def obter_conquistas(self, steamid64, appid):
        """Retorna os contadores de conquistas de um jogo para o usuário.

        O endpoint GetPlayerAchievements devolve a lista de conquistas do
        aplicativo com o campo ``achieved`` (0/1). Quando o jogo não possui
        conquistas, as estatísticas estão privadas ou a Steam não disponibiliza
        esses dados, retorna ``None`` para que uma sincronização não apague
        valores que já existam no SavePoint.
        """
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

            # Para jogos sem conquistas/estatísticas ou dados não acessíveis,
            # a Steam pode responder 400/403. Isso não deve abortar a importação.
            if getattr(resp, "status_code", 200) in (400, 403):
                return None

            resp.raise_for_status()
            playerstats = resp.json().get("playerstats", {})
        except requests.RequestException as exc:
            raise SteamErroDeComunicacao(f"Falha ao consultar conquistas na Steam: {exc}") from exc

        if playerstats.get("success") is False:
            return None

        conquistas = playerstats.get("achievements")
        if not isinstance(conquistas, list):
            return None

        return {
            "total_conquistas": len(conquistas),
            "conquistas_obtidas": sum(
                1 for conquista in conquistas if conquista.get("achieved") == 1
            ),
        }

