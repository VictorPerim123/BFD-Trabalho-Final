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


def test_perfil_privado_vira_erro_explicativo(monkeypatch):
    # a Steam responde 200 com um objeto vazio quando a biblioteca é privada
    monkeypatch.setattr(steam_service.requests, "get", lambda *a, **kw: RespostaFalsa({"response": {}}))

    with pytest.raises(SteamPerfilIndisponivel):
        SteamService("chave-de-teste").obter_biblioteca("76561197960287930")


def test_biblioteca_arredonda_meia_hora_para_cima(monkeypatch):
    payload = {
        "response": {
            "games": [
                {"appid": 1, "name": "Meia hora", "playtime_forever": 30},
                {"appid": 2, "name": "Uma hora e meia", "playtime_forever": 90},
            ]
        }
    }
    monkeypatch.setattr(steam_service.requests, "get", lambda *a, **kw: RespostaFalsa(payload))

    jogos = SteamService("chave-de-teste").obter_biblioteca("76561197960287930")

    assert jogos[0]["tempo_jogado_horas"] == 1
    assert jogos[1]["tempo_jogado_horas"] == 2
