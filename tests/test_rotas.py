from app.extensions import db
from app.models import Jogo, Usuario


def test_detalhe_exige_login(client, app):
    with app.app_context():
        usuario = Usuario(nome="Teste", username="rota", email="rota@savepoint.dev")
        usuario.set_senha("SenhaForte123")
        db.session.add(usuario)
        db.session.commit()
        jogo = Jogo(usuario_id=usuario.id, titulo="Jogo")
        db.session.add(jogo)
        db.session.commit()
        jogo_id = jogo.id

    resposta = client.get(f"/jogos/{jogo_id}")
    assert resposta.status_code in (302, 303)


def test_detalhe_nao_expoe_jogo_de_outro_usuario(client_autenticado, app):
    with app.app_context():
        outro = Usuario(nome="Outro", username="rotaoutro", email="rotaoutro@savepoint.dev")
        outro.set_senha("SenhaForte123")
        db.session.add(outro)
        db.session.commit()
        jogo = Jogo(usuario_id=outro.id, titulo="Privado")
        db.session.add(jogo)
        db.session.commit()
        jogo_id = jogo.id

    resposta = client_autenticado.get(f"/jogos/{jogo_id}")
    assert resposta.status_code == 404


def test_jornada_unifica_builds_e_runs(client_autenticado):
    resposta = client_autenticado.get("/jornada")
    assert resposta.status_code == 200
    assert b"Jornada" in resposta.data
    assert b"Builds" in resposta.data
    assert b"Runs" in resposta.data


def test_rotas_antigas_de_runs_e_builds_redirecionam_para_jornada(client_autenticado):
    runs = client_autenticado.get("/runs")
    builds = client_autenticado.get("/builds")
    nova_run = client_autenticado.get("/runs/novo?jogo_id=12")

    assert runs.status_code in (302, 303)
    assert "/jornada" in runs.headers["Location"]
    assert builds.status_code in (302, 303)
    assert "/jornada" in builds.headers["Location"]
    assert nova_run.status_code in (302, 303)
    assert "aba=runs" in nova_run.headers["Location"]
    assert "jogo_id=12" in nova_run.headers["Location"]


def test_detalhe_exibe_navegacao_por_abas(client_autenticado, app, usuario):
    with app.app_context():
        jogo = Jogo(usuario_id=usuario.id, titulo="Com abas")
        db.session.add(jogo)
        db.session.commit()
        jogo_id = jogo.id

    resposta = client_autenticado.get(f"/jogos/{jogo_id}")

    assert resposta.status_code == 200
    assert b"Vis\xc3\xa3o geral" in resposta.data
    assert b"Conquistas" in resposta.data
    assert b"Jornada" in resposta.data
    assert b"Desafios" in resposta.data
    assert b"Hist\xc3\xb3rico" in resposta.data


def test_importacao_steam_exibe_previa_sem_aplicar_sincronizacao(client_autenticado, monkeypatch):
    class SteamSyncFalso:
        def __init__(self, usuario, api_key):
            self.usuario = usuario

        def previsualizar(self, identificador, **opcoes):
            return {
                "steam_id": "76561197960287930",
                "encontrados": 3,
                "novos": 1,
                "vinculaveis": 1,
                "existentes": 1,
                "atualizacoes_previstas": 2,
                "sem_alteracao_prevista": 0,
                "status_reclassificados": 1,
                "status_preservados": 1,
                "status_previstos": {
                    "quero_jogar": 0,
                    "jogando": 1,
                    "jogado": 0,
                    "zerado": 0,
                    "platinado": 1,
                    "abandonado": 0,
                },
                "falhas_conquistas": 0,
                "classificacao_automatica": True,
                "reclassificar_existentes": True,
            }

        def sincronizar(self, identificador, **opcoes):
            raise AssertionError("A prévia não deve aplicar a sincronização")

    monkeypatch.setattr("app.routes.steam.SteamSyncService", SteamSyncFalso)

    resposta = client_autenticado.post(
        "/steam/importar",
        data={
            "acao": "previsualizar",
            "identificador": "perfil",
            "classificacao_status": "automatico",
            "reclassificar_existentes": "1",
        },
    )

    assert resposta.status_code == 200
    assert b"Pr\xc3\xa9via da sincroniza\xc3\xa7\xc3\xa3o" in resposta.data
    assert b"Nenhuma altera\xc3\xa7\xc3\xa3o foi aplicada ainda" in resposta.data
    assert b"Confirmar sincroniza\xc3\xa7\xc3\xa3o" in resposta.data
    assert b'id="steam-preview-form"' not in resposta.data


def test_importacao_steam_modal_retorna_conteudo_parcial(client_autenticado):
    resposta = client_autenticado.get("/steam/importar?modal=1")

    assert resposta.status_code == 200
    assert b"data-steam-import-root" in resposta.data
    assert b"modo_modal" in resposta.data
    assert b"<html" not in resposta.data.lower()


def test_backlog_e_desafios_exibem_formularios_em_dialog(client_autenticado):
    backlog = client_autenticado.get("/backlog")
    desafios = client_autenticado.get("/desafios")

    assert backlog.status_code == 200
    assert b'<dialog class="app-modal app-modal--wide" id="game-form-card"' in backlog.data
    assert desafios.status_code == 200
    assert b'<dialog class="app-modal app-modal--wide" id="challenge-form-card"' in desafios.data
