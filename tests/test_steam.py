import pytest

from app.services import steam_service
from app.services.steam_service import (
    SteamNaoConfigurado,
    SteamPerfilIndisponivel,
    SteamService,
)


class RespostaFalsa:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_servico_sem_chave_configurada_falha_na_criacao():
    with pytest.raises(SteamNaoConfigurado):
        SteamService("")


def test_biblioteca_traz_tempo_capa_e_conquistas(monkeypatch):
    biblioteca = {
        "response": {
            "games": [
                {"appid": 1245620, "name": "ELDEN RING", "playtime_forever": 3720},
                {"appid": 1145360, "name": "Hades", "playtime_forever": 45},
            ]
        }
    }

    def get_falso(url, params=None, **_kwargs):
        if "GetOwnedGames" in url:
            return RespostaFalsa(biblioteca)
        if "GetPlayerAchievements" in url:
            if params["appid"] == 1245620:
                return RespostaFalsa(
                    {
                        "playerstats": {
                            "success": True,
                            "achievements": [
                                {"apiname": "A", "achieved": 1},
                                {"apiname": "B", "achieved": 0},
                                {"apiname": "C", "achieved": 1},
                            ],
                        }
                    }
                )
            return RespostaFalsa(
                {"playerstats": {"success": False, "error": "Requested app has no stats"}}
            )
        if url == steam_service.STORE_API_URL:
            appid = params["appids"]
            return RespostaFalsa(
                {str(appid): {"success": True, "data": {"header_image": f"https://img/{appid}.jpg"}}}
            )
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr(steam_service.requests, "get", get_falso)

    jogos = SteamService("chave-de-teste").obter_biblioteca("76561197960287930")

    assert jogos[0] == {
        "steam_appid": 1245620,
        "titulo": "ELDEN RING",
        "tempo_jogado_horas": 62,
        "capa_url": "https://img/1245620.jpg",
        "total_conquistas": 3,
        "conquistas_obtidas": 2,
        "conquistas_sincronizadas": True,
    }
    assert jogos[1]["tempo_jogado_horas"] == 1
    assert jogos[1]["total_conquistas"] == 0
    assert jogos[1]["conquistas_sincronizadas"] is True


def test_perfil_privado_vira_erro_explicativo(monkeypatch):
    monkeypatch.setattr(
        steam_service.requests,
        "get",
        lambda *a, **kw: RespostaFalsa({"response": {}}),
    )

    with pytest.raises(SteamPerfilIndisponivel):
        SteamService("chave-de-teste").obter_biblioteca("76561197960287930")


def test_biblioteca_arredonda_meia_hora_para_cima(monkeypatch):
    biblioteca = {
        "response": {
            "games": [
                {"appid": 1, "name": "Meia hora", "playtime_forever": 30},
                {"appid": 2, "name": "Uma hora e meia", "playtime_forever": 90},
            ]
        }
    }

    def get_falso(url, params=None, **_kwargs):
        if "GetOwnedGames" in url:
            return RespostaFalsa(biblioteca)
        if "GetPlayerAchievements" in url:
            return RespostaFalsa(
                {"playerstats": {"success": False, "error": "Requested app has no stats"}}
            )
        if url == steam_service.STORE_API_URL:
            return RespostaFalsa({})
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr(steam_service.requests, "get", get_falso)

    jogos = SteamService("chave-de-teste").obter_biblioteca("76561197960287930")

    assert jogos[0]["tempo_jogado_horas"] == 1
    assert jogos[1]["tempo_jogado_horas"] == 2


def test_falha_em_conquistas_nao_marca_sincronizacao(monkeypatch):
    biblioteca = {
        "response": {"games": [{"appid": 10, "name": "Teste", "playtime_forever": 0}]}
    }

    def get_falso(url, params=None, **_kwargs):
        if "GetOwnedGames" in url:
            return RespostaFalsa(biblioteca)
        if "GetPlayerAchievements" in url:
            raise steam_service.requests.RequestException("indisponível")
        if url == steam_service.STORE_API_URL:
            return RespostaFalsa({})
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr(steam_service.requests, "get", get_falso)

    [jogo] = SteamService("chave-de-teste").obter_biblioteca("76561197960287930")

    assert jogo["conquistas_sincronizadas"] is False
    assert jogo["total_conquistas"] == 0
    assert jogo["capa_url"].endswith("/10/header.jpg")

def test_resolver_steamid_aceita_url_de_profile_numerico(monkeypatch):
    monkeypatch.setattr(
        steam_service.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("requisição inesperada")),
    )

    steamid = SteamService("chave-de-teste").resolver_steamid(
        "https://steamcommunity.com/profiles/76561197960287930/?utm_source=teste"
    )

    assert steamid == "76561197960287930"


def test_resolver_steamid_rejeita_entrada_vazia():
    with pytest.raises(SteamPerfilIndisponivel):
        SteamService("chave-de-teste").resolver_steamid("  ")
