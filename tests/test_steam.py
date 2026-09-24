import pytest

from app.services import steam_service
from app.services.steam_service import (
    SteamNaoConfigurado,
    SteamPerfilIndisponivel,
    SteamService,
)


class RespostaFalsa:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise steam_service.requests.HTTPError(f"HTTP {self.status_code}")

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
                                {"apiname": "A", "achieved": 1, "name": "Primeira", "description": "Descrição A", "unlocktime": 1700000000},
                                {"apiname": "B", "achieved": 0, "name": "Segunda"},
                                {"apiname": "C", "achieved": 1, "name": "Terceira"},
                            ],
                        }
                    }
                )
            return RespostaFalsa(
                {"playerstats": {"success": False, "error": "Requested app has no stats"}}
            )
        if "GetSchemaForGame" in url:
            if params["appid"] == 1245620:
                return RespostaFalsa(
                    {
                        "game": {
                            "availableGameStats": {
                                "achievements": [
                                    {"name": "A", "displayName": "Primeira", "description": "Descrição A", "icon": "https://img/a.jpg", "icongray": "https://img/a-gray.jpg"},
                                    {"name": "B", "displayName": "Segunda", "icon": "https://img/b.jpg", "icongray": "https://img/b-gray.jpg"},
                                    {"name": "C", "displayName": "Terceira", "icon": "https://img/c.jpg", "icongray": "https://img/c-gray.jpg"},
                                ]
                            }
                        }
                    }
                )
            return RespostaFalsa({"game": {}})
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
        "tempo_jogado_minutos": 3720,
        "atividade_recente": False,
        "atividade_recente_disponivel": False,
        "capa_url": "https://img/1245620.jpg",
        "total_conquistas": 3,
        "conquistas_obtidas": 2,
        "conquistas_sincronizadas": True,
        "conquistas_disponiveis": True,
        "conquistas_detalhes": [
            {
                "api_name": "A",
                "nome": "Primeira",
                "descricao": "Descrição A",
                "icone_url": "https://img/a.jpg",
                "icone_bloqueada_url": "https://img/a-gray.jpg",
                "desbloqueada": True,
                "unlocktime": 1700000000,
            },
            {
                "api_name": "B",
                "nome": "Segunda",
                "descricao": None,
                "icone_url": "https://img/b.jpg",
                "icone_bloqueada_url": "https://img/b-gray.jpg",
                "desbloqueada": False,
                "unlocktime": None,
            },
            {
                "api_name": "C",
                "nome": "Terceira",
                "descricao": None,
                "icone_url": "https://img/c.jpg",
                "icone_bloqueada_url": "https://img/c-gray.jpg",
                "desbloqueada": True,
                "unlocktime": None,
            },
        ],
    }
    assert jogos[1]["tempo_jogado_horas"] == 1
    assert jogos[1]["total_conquistas"] == 0
    assert jogos[1]["conquistas_sincronizadas"] is True
    assert jogos[1]["conquistas_disponiveis"] is False
    assert jogos[1]["conquistas_detalhes"] == []


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
        if "GetSchemaForGame" in url:
            return RespostaFalsa({"game": {}})
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
    assert jogo["conquistas_disponiveis"] is False
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


def test_conquistas_interpreta_no_stats_mesmo_com_http_400(monkeypatch):
    monkeypatch.setattr(
        steam_service.requests,
        "get",
        lambda *args, **kwargs: RespostaFalsa(
            {"playerstats": {"success": False, "error": "Requested app has no stats"}},
            status_code=400,
        ),
    )

    resultado = SteamService("chave-de-teste")._obter_conquistas(
        "76561197960287930", 10
    )

    assert resultado == (0, 0, False, [])


def test_conquistas_repete_apos_429_e_processa_resposta_valida(monkeypatch):
    respostas = [
        RespostaFalsa({"error": "rate limit"}, status_code=429),
        RespostaFalsa(
            {
                "playerstats": {
                    "success": True,
                    "achievements": [
                        {"apiname": "A", "achieved": 1},
                        {"apiname": "B", "achieved": "1"},
                        {"apiname": "C", "achieved": 0},
                    ],
                }
            }
        ),
    ]

    def get_falso(url, *args, **kwargs):
        if "GetSchemaForGame" in url:
            return RespostaFalsa({"game": {}})
        return respostas.pop(0)

    monkeypatch.setattr(steam_service.requests, "get", get_falso)
    monkeypatch.setattr(steam_service.time, "sleep", lambda *_args: None)

    resultado = SteamService("chave-de-teste")._obter_conquistas(
        "76561197960287930", 10
    )

    assert resultado[:3] == (3, 2, True)
    assert [item["api_name"] for item in resultado[3]] == ["A", "B", "C"]
    assert respostas == []


def test_biblioteca_pode_marcar_atividade_recente(monkeypatch):
    biblioteca = {
        "response": {
            "games": [
                {"appid": 1, "name": "Recente", "playtime_forever": 15},
                {"appid": 2, "name": "Antigo", "playtime_forever": 120},
            ]
        }
    }

    def get_falso(url, params=None, **_kwargs):
        if "GetOwnedGames" in url:
            return RespostaFalsa(biblioteca)
        if "GetRecentlyPlayedGames" in url:
            return RespostaFalsa({"response": {"games": [{"appid": 1}]}})
        if "GetPlayerAchievements" in url:
            return RespostaFalsa({"playerstats": {"success": False, "error": "Requested app has no stats"}})
        if url == steam_service.STORE_API_URL:
            return RespostaFalsa({})
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr(steam_service.requests, "get", get_falso)

    jogos = SteamService("chave-de-teste").obter_biblioteca(
        "76561197960287930", incluir_atividade_recente=True
    )

    assert jogos[0]["atividade_recente"] is True
    assert jogos[0]["atividade_recente_disponivel"] is True
    assert jogos[0]["tempo_jogado_minutos"] == 15
    assert jogos[1]["atividade_recente"] is False


def test_biblioteca_para_previa_nao_consulta_capa_nem_schema(monkeypatch):
    biblioteca = {
        "response": {
            "games": [{"appid": 500, "name": "Prévia", "playtime_forever": 60}]
        }
    }
    chamadas = []

    def get_falso(url, params=None, **_kwargs):
        chamadas.append(url)
        if "GetOwnedGames" in url:
            return RespostaFalsa(biblioteca)
        if "GetPlayerAchievements" in url:
            return RespostaFalsa(
                {
                    "playerstats": {
                        "success": True,
                        "achievements": [
                            {"apiname": "A", "achieved": 1},
                            {"apiname": "B", "achieved": 0},
                        ],
                    }
                }
            )
        raise AssertionError(f"A prévia não deveria consultar {url}")

    monkeypatch.setattr(steam_service.requests, "get", get_falso)

    [jogo] = SteamService("chave-de-teste").obter_biblioteca(
        "76561197960287930",
        incluir_capas=False,
        incluir_detalhes_conquistas=False,
    )

    assert jogo["total_conquistas"] == 2
    assert jogo["conquistas_obtidas"] == 1
    assert jogo["conquistas_detalhes"] == []
    assert not any("GetSchemaForGame" in url for url in chamadas)
    assert not any(url == steam_service.STORE_API_URL for url in chamadas)
