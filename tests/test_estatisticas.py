from app.extensions import db
from app.models import Usuario
from app.services.backlog_service import BacklogService


def _servico(app_context_usuario="carla"):
    usuario = Usuario(
        nome="Carla",
        username=app_context_usuario,
        email=f"{app_context_usuario}@savepoint.dev",
    )
    usuario.set_senha("SenhaForte123")
    db.session.add(usuario)
    db.session.commit()
    return BacklogService(usuario)


def test_jogo_platinado_tambem_conta_como_zerado(app):
    with app.app_context():
        servico = _servico()
        servico.criar_jogo({"titulo": "Cyberpunk 2077", "status": "zerado"})
        servico.criar_jogo({"titulo": "Baldur's Gate 3", "status": "platinado"})
        servico.criar_jogo({"titulo": "Hades II", "status": "quero_jogar"})

        stats = servico.calcular_estatisticas_dashboard()
        assert stats["jogos_zerados"] == 2


def test_horas_totais_somam_o_tempo_de_todos_os_jogos(app):
    with app.app_context():
        servico = _servico()
        servico.criar_jogo({"titulo": "Elden Ring", "tempo_jogado_horas": 62})
        servico.criar_jogo({"titulo": "Dead Cells", "tempo_jogado_horas": 18})

        stats = servico.calcular_estatisticas_dashboard()
        assert stats["horas_totais"] == 80


def test_nota_media_e_none_quando_nenhum_jogo_foi_avaliado(app):
    with app.app_context():
        servico = _servico()
        servico.criar_jogo({"titulo": "Jogo Sem Nota"})

        stats = servico.calcular_estatisticas_dashboard()
        assert stats["nota_media"] is None


def test_nota_media_ignora_jogos_sem_nota(app):
    with app.app_context():
        servico = _servico()
        servico.criar_jogo({"titulo": "Jogo A", "nota": 8})
        servico.criar_jogo({"titulo": "Jogo B", "nota": 10})
        servico.criar_jogo({"titulo": "Jogo C"})

        stats = servico.calcular_estatisticas_dashboard()
        assert stats["nota_media"] == 9.0


def test_endpoint_de_estatisticas_exige_sessao(client):
    assert client.get("/api/estatisticas").status_code == 401


def test_endpoint_de_estatisticas_devolve_os_quatro_numeros(client_autenticado):
    client_autenticado.post(
        "/api/jogos",
        json={"titulo": "Hollow Knight", "status": "zerado", "nota": 9.5},
    )

    resposta = client_autenticado.get("/api/estatisticas")
    assert resposta.status_code == 200

    corpo = resposta.get_json()
    assert corpo["jogos_zerados"] == 1
    assert corpo["nota_media"] == 9.5
    assert corpo["total_runs"] == 0
    assert "horas_totais" in corpo
