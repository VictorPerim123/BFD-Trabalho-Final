import pytest

from app.extensions import db
from app.models import Usuario, Categoria
from app.services.backlog_service import BacklogService, ErroDeValidacao


def _criar_usuario(username="bia"):
    usuario = Usuario(nome="Bia", username=username, email=f"{username}@savepoint.dev")
    usuario.set_senha("SenhaForte123")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def test_criar_jogo_sem_titulo_levanta_erro_de_validacao(app):
    with app.app_context():
        servico = BacklogService(_criar_usuario())
        with pytest.raises(ErroDeValidacao):
            servico.criar_jogo({"titulo": "   "})


def test_criar_jogo_com_nota_fora_do_intervalo_levanta_erro(app):
    with app.app_context():
        servico = BacklogService(_criar_usuario())
        with pytest.raises(ErroDeValidacao):
            servico.criar_jogo({"titulo": "Jogo Teste", "nota": 15})


def test_criar_jogo_com_status_invalido_levanta_erro(app):
    with app.app_context():
        servico = BacklogService(_criar_usuario())
        with pytest.raises(ErroDeValidacao):
            servico.criar_jogo({"titulo": "Jogo Teste", "status": "concluido-com-100%"})


def test_percentual_conquistas_e_calculado_corretamente(app):
    with app.app_context():
        servico = BacklogService(_criar_usuario())
        jogo = servico.criar_jogo(
            {"titulo": "Hades", "total_conquistas": 40, "conquistas_obtidas": 10}
        )
        assert jogo.percentual_conquistas == 25


def test_percentual_conquistas_e_zero_quando_jogo_nao_rastreia_conquistas(app):
    with app.app_context():
        servico = BacklogService(_criar_usuario())
        jogo = servico.criar_jogo({"titulo": "Jogo Sem Conquistas"})
        assert jogo.percentual_conquistas == 0


def test_categorias_repetidas_nao_sao_duplicadas_para_o_mesmo_usuario(app):
    with app.app_context():
        usuario = _criar_usuario()
        servico = BacklogService(usuario)

        servico.criar_jogo({"titulo": "Jogo A", "categorias": ["RPG"]})
        servico.criar_jogo({"titulo": "Jogo B", "categorias": ["RPG", "Ação"]})

        total_rpg = Categoria.query.filter_by(usuario_id=usuario.id, nome="RPG").count()
        assert total_rpg == 1
