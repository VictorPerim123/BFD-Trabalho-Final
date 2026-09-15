"""
tests/test_steam.py — a integração externa é testada com a rede desligada:
substituímos requests.get por uma resposta falsa (monkeypatch). Os testes não
dependem de chave da Steam, de internet nem do perfil de ninguém.
"""

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
        return None

    def json(self):
        return self._payload


def test_servico_sem_chave_configurada_falha_na_criacao():
    with pytest.raises(SteamNaoConfigurado):
        SteamService("")


def test_biblioteca_converte_minutos_em_horas(monkeypatch):
    payload = {
        "response": {
            "games": [
                {"appid": 1245620, "name": "ELDEN RING", "playtime_forever": 3720},
                {"appid": 1145360, "name": "Hades", "playtime_forever": 45},
            ]
        }
    }
    monkeypatch.setattr(steam_service.requests, "get", lambda *a, **kw: RespostaFalsa(payload))

    jogos = SteamService("chave-de-teste").obter_biblioteca("76561197960287930")

    assert jogos[0] == {
        "steam_appid": 1245620,
        "titulo": "ELDEN RING",
        "tempo_jogado_horas": 62,
    }
    assert jogos[1]["tempo_jogado_horas"] == 1


def test_conquistas_conta_total_e_obtidas(monkeypatch):
    payload = {
        "playerstats": {
            "success": True,
            "achievements": [
                {"apiname": "ACH_1", "achieved": 1},
                {"apiname": "ACH_2", "achieved": 0},
                {"apiname": "ACH_3", "achieved": 1},
            ],
        }
    }
    monkeypatch.setattr(steam_service.requests, "get", lambda *a, **kw: RespostaFalsa(payload))

    contadores = SteamService("chave-de-teste").obter_conquistas(
        "76561197960287930", 1145360
    )

    assert contadores == {
        "total_conquistas": 3,
        "conquistas_obtidas": 2,
    }


def test_conquistas_indisponiveis_nao_viram_zero(monkeypatch):
    payload = {"playerstats": {"success": False, "error": "Requested app has no stats"}}
    monkeypatch.setattr(steam_service.requests, "get", lambda *a, **kw: RespostaFalsa(payload))

    contadores = SteamService("chave-de-teste").obter_conquistas(
        "76561197960287930", 10
    )

    assert contadores is None


def test_perfil_privado_vira_erro_explicativo(monkeypatch):
    # a Steam responde 200 com um objeto vazio quando a biblioteca é privada
    monkeypatch.setattr(steam_service.requests, "get", lambda *a, **kw: RespostaFalsa({"response": {}}))

    with pytest.raises(SteamPerfilIndisponivel):
        SteamService("chave-de-teste").obter_biblioteca("76561197960287930")


def test_reimportacao_atualiza_tempo_sem_sobrescrever_dados_pessoais(
    client_autenticado, usuario, app, monkeypatch
):
    from app.extensions import db
    from app.models import Jogo

    with app.app_context():
        jogo = Jogo(
            usuario_id=usuario.id,
            titulo="Hades",
            status="jogando",
            nota=9.5,
            tempo_jogado_horas=20,
            total_conquistas=49,
            conquistas_obtidas=20,
            steam_appid=1145360,
        )
        db.session.add(jogo)
        db.session.commit()
        jogo_id = jogo.id

    app.config["STEAM_API_KEY"] = "chave-de-teste"
    monkeypatch.setattr(SteamService, "resolver_steamid", lambda self, entrada: "76561197960287930")
    monkeypatch.setattr(
        SteamService,
        "obter_biblioteca",
        lambda self, steamid: [
            {
                "steam_appid": 1145360,
                "titulo": "Hades",
                "tempo_jogado_horas": 35,
            }
        ],
    )
    monkeypatch.setattr(
        SteamService,
        "obter_conquistas",
        lambda self, steamid, appid: {
            "total_conquistas": 49,
            "conquistas_obtidas": 27,
        },
    )

    resposta = client_autenticado.post(
        "/steam/importar",
        data={"identificador": "76561197960287930"},
    )

    assert resposta.status_code == 200
    assert b"1 jogo(s) sincronizado(s)" in resposta.data
    assert b"conquistas atualizadas em 1 jogo(s)" in resposta.data

    with app.app_context():
        atualizado = db.session.get(Jogo, jogo_id)
        assert atualizado.tempo_jogado_horas == 35
        assert atualizado.total_conquistas == 49
        assert atualizado.conquistas_obtidas == 27
        assert atualizado.status == "jogando"
        assert atualizado.nota == 9.5

def test_reimportacao_preserva_conquistas_quando_steam_nao_disponibiliza(
    client_autenticado, usuario, app, monkeypatch
):
    from app.extensions import db
    from app.models import Jogo

    with app.app_context():
        jogo = Jogo(
            usuario_id=usuario.id,
            titulo="Jogo sem stats acessiveis",
            status="jogando",
            tempo_jogado_horas=10,
            total_conquistas=30,
            conquistas_obtidas=12,
            steam_appid=999999,
        )
        db.session.add(jogo)
        db.session.commit()
        jogo_id = jogo.id

    app.config["STEAM_API_KEY"] = "chave-de-teste"
    monkeypatch.setattr(SteamService, "resolver_steamid", lambda self, entrada: "76561197960287930")
    monkeypatch.setattr(
        SteamService,
        "obter_biblioteca",
        lambda self, steamid: [
            {
                "steam_appid": 999999,
                "titulo": "Jogo sem stats acessiveis",
                "tempo_jogado_horas": 15,
            }
        ],
    )
    monkeypatch.setattr(SteamService, "obter_conquistas", lambda self, steamid, appid: None)

    resposta = client_autenticado.post(
        "/steam/importar",
        data={"identificador": "76561197960287930"},
    )

    assert resposta.status_code == 200
    assert b"Em 1 jogo(s), as conquistas n" in resposta.data

    with app.app_context():
        atualizado = db.session.get(Jogo, jogo_id)
        assert atualizado.tempo_jogado_horas == 15
        assert atualizado.total_conquistas == 30
        assert atualizado.conquistas_obtidas == 12

