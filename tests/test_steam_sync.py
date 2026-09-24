from app.extensions import db
from app.models import Jogo, Usuario
from app.services.steam_sync_service import SteamSyncService


def test_sincronizacao_steam_orquestra_biblioteca_e_persistencia(app, monkeypatch):
    with app.app_context():
        usuario = Usuario(nome="Steam", username="steamuser", email="steam@savepoint.dev")
        usuario.set_senha("SenhaForte123")
        db.session.add(usuario)
        db.session.commit()

        servico = SteamSyncService(usuario, "chave")
        monkeypatch.setattr(servico.steam, "resolver_steamid", lambda identificador: "76561197960287930")
        monkeypatch.setattr(
            servico.steam,
            "obter_biblioteca",
            lambda steamid, incluir_atividade_recente=False: [
                {
                    "steam_appid": 10,
                    "titulo": "Jogo Steam",
                    "tempo_jogado_horas": 5,
                    "capa_url": "https://cdn.example/jogo.jpg",
                    "total_conquistas": 3,
                    "conquistas_obtidas": 1,
                    "conquistas_sincronizadas": True,
                    "conquistas_disponiveis": True,
                }
            ],
        )

        resultado = servico.sincronizar("perfil")

        assert resultado["encontrados"] == 1
        assert resultado["importados"] == 1
        assert usuario.steam_id == "76561197960287930"
        assert Jogo.query.filter_by(usuario_id=usuario.id, steam_appid=10).count() == 1


def test_sincronizacao_steam_classificacao_automatica_solicita_atividade_recente(app, monkeypatch):
    with app.app_context():
        usuario = Usuario(nome="Status", username="steamstatus", email="steamstatus@savepoint.dev")
        usuario.set_senha("SenhaForte123")
        db.session.add(usuario)
        db.session.commit()

        servico = SteamSyncService(usuario, "chave")
        monkeypatch.setattr(servico.steam, "resolver_steamid", lambda identificador: "76561197960287930")
        chamadas = []

        def biblioteca(steamid, incluir_atividade_recente=False):
            chamadas.append(incluir_atividade_recente)
            return [
                {
                    "steam_appid": 30,
                    "titulo": "Jogado",
                    "tempo_jogado_horas": 0,
                    "tempo_jogado_minutos": 15,
                    "atividade_recente": False,
                }
            ]

        monkeypatch.setattr(servico.steam, "obter_biblioteca", biblioteca)
        resultado = servico.sincronizar("perfil", classificar_status=True)

        jogo = Jogo.query.filter_by(usuario_id=usuario.id, steam_appid=30).one()
        assert chamadas == [True]
        assert jogo.status == "jogado"
        assert resultado["status_classificados"] == 1


def test_previa_steam_usa_consulta_reduzida_e_nao_salva_steam_id(app, monkeypatch):
    with app.app_context():
        usuario = Usuario(nome="Prévia", username="previastream", email="previa@savepoint.dev")
        usuario.set_senha("SenhaForte123")
        db.session.add(usuario)
        db.session.commit()

        servico = SteamSyncService(usuario, "chave")
        monkeypatch.setattr(servico.steam, "resolver_steamid", lambda identificador: "76561197960287930")
        chamadas = []

        def biblioteca(steamid, incluir_atividade_recente=False, **opcoes):
            chamadas.append((incluir_atividade_recente, opcoes))
            return [
                {
                    "steam_appid": 401,
                    "titulo": "Prévia",
                    "tempo_jogado_horas": 2,
                    "tempo_jogado_minutos": 120,
                    "atividade_recente": True,
                    "total_conquistas": 10,
                    "conquistas_obtidas": 3,
                    "conquistas_sincronizadas": True,
                }
            ]

        monkeypatch.setattr(servico.steam, "obter_biblioteca", biblioteca)
        resultado = servico.previsualizar("perfil", classificar_status=True)

        assert chamadas == [
            (
                True,
                {"incluir_capas": False, "incluir_detalhes_conquistas": False},
            )
        ]
        assert resultado["encontrados"] == 1
        assert resultado["novos"] == 1
        assert usuario.steam_id is None
        assert Jogo.query.filter_by(usuario_id=usuario.id).count() == 0
