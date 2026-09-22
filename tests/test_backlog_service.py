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


def test_valores_numericos_invalidos_sao_rejeitados(app):
    with app.app_context():
        servico = BacklogService(_criar_usuario())
        with pytest.raises(ErroDeValidacao):
            servico.criar_jogo({"titulo": "Jogo", "tempo_jogado_horas": "muitas"})
        with pytest.raises(ErroDeValidacao):
            servico.criar_jogo({"titulo": "Jogo", "total_conquistas": -1})


def test_conquistas_obtidas_nao_podem_ultrapassar_total(app):
    with app.app_context():
        servico = BacklogService(_criar_usuario())
        with pytest.raises(ErroDeValidacao):
            servico.criar_jogo(
                {"titulo": "Jogo", "total_conquistas": 10, "conquistas_obtidas": 11}
            )


def test_categorias_ignoram_diferenca_de_maiusculas_e_minusculas(app):
    with app.app_context():
        usuario = _criar_usuario()
        servico = BacklogService(usuario)
        servico.criar_jogo({"titulo": "Jogo A", "categorias": ["RPG"]})
        jogo_b = servico.criar_jogo({"titulo": "Jogo B", "categorias": ["rpg", "Rpg"]})

        assert Categoria.query.filter_by(usuario_id=usuario.id).count() == 1
        assert len(jogo_b.categorias) == 1
        assert jogo_b.categorias[0].nome == "RPG"


def test_categorias_unicode_ignoram_diferenca_de_maiusculas(app):
    with app.app_context():
        usuario = _criar_usuario()
        servico = BacklogService(usuario)

        servico.criar_jogo({"titulo": "Jogo A", "categorias": ["Ação"]})
        jogo_b = servico.criar_jogo({"titulo": "Jogo B", "categorias": ["AÇÃO", "ação"]})

        categorias = Categoria.query.filter_by(usuario_id=usuario.id).all()
        assert len(categorias) == 1
        assert categorias[0].nome == "Ação"
        assert len(jogo_b.categorias) == 1


def test_importacao_steam_associa_jogo_manual_sem_duplicar(app):
    from app.models import Jogo

    with app.app_context():
        usuario = _criar_usuario()
        servico = BacklogService(usuario)
        manual = servico.criar_jogo({"titulo": "Hades", "tempo_jogado_horas": 5})

        resultado = servico.importar_jogos_steam(
            [{"steam_appid": 1145360, "titulo": "HADES", "tempo_jogado_horas": 20}]
        )

        assert resultado == {"importados": 0, "vinculados": 1, "atualizados": 0, "ignorados": 0}
        assert Jogo.query.filter_by(usuario_id=usuario.id).count() == 1
        assert manual.steam_appid == 1145360
        assert manual.tempo_jogado_horas == 20


def test_importacao_steam_nao_reduz_tempo_manual_ao_associar(app):
    with app.app_context():
        usuario = _criar_usuario()
        servico = BacklogService(usuario)
        manual = servico.criar_jogo({"titulo": "Hades", "tempo_jogado_horas": 50})

        servico.importar_jogos_steam(
            [{"steam_appid": 1145360, "titulo": "Hades", "tempo_jogado_horas": 20}]
        )

        assert manual.tempo_jogado_horas == 50


def test_importacao_steam_repetida_ignora_appid_ja_associado(app):
    from app.models import Jogo

    with app.app_context():
        usuario = _criar_usuario()
        servico = BacklogService(usuario)
        biblioteca = [{"steam_appid": 1145360, "titulo": "Hades", "tempo_jogado_horas": 20}]

        primeira = servico.importar_jogos_steam(biblioteca)
        segunda = servico.importar_jogos_steam(biblioteca)

        assert primeira == {"importados": 1, "vinculados": 0, "atualizados": 0, "ignorados": 0}
        assert segunda == {"importados": 0, "vinculados": 0, "atualizados": 0, "ignorados": 1}
        assert Jogo.query.filter_by(usuario_id=usuario.id).count() == 1



def test_importacao_steam_atualiza_capa_e_conquistas_de_appid_existente(app):
    with app.app_context():
        usuario = _criar_usuario()
        servico = BacklogService(usuario)
        jogo = servico.criar_jogo(
            {
                "titulo": "Hades",
                "tempo_jogado_horas": 20,
                "steam_appid": 1145360,
                "total_conquistas": 10,
                "conquistas_obtidas": 2,
            }
        )

        resultado = servico.importar_jogos_steam(
            [
                {
                    "steam_appid": 1145360,
                    "titulo": "Hades",
                    "tempo_jogado_horas": 25,
                    "capa_url": "https://cdn.example/hades.jpg",
                    "total_conquistas": 49,
                    "conquistas_obtidas": 31,
                    "conquistas_sincronizadas": True,
                }
            ]
        )

        assert resultado == {
            "importados": 0,
            "vinculados": 0,
            "atualizados": 1,
            "ignorados": 0,
        }
        assert jogo.tempo_jogado_horas == 25
        assert jogo.capa_url == "https://cdn.example/hades.jpg"
        assert jogo.total_conquistas == 49
        assert jogo.conquistas_obtidas == 31


def test_importacao_steam_nao_zera_conquistas_quando_api_falha(app):
    with app.app_context():
        usuario = _criar_usuario()
        servico = BacklogService(usuario)
        jogo = servico.criar_jogo(
            {
                "titulo": "Hades",
                "steam_appid": 1145360,
                "total_conquistas": 49,
                "conquistas_obtidas": 31,
            }
        )

        servico.importar_jogos_steam(
            [
                {
                    "steam_appid": 1145360,
                    "titulo": "Hades",
                    "tempo_jogado_horas": 0,
                    "total_conquistas": 0,
                    "conquistas_obtidas": 0,
                    "conquistas_sincronizadas": False,
                }
            ]
        )

        assert jogo.total_conquistas == 49
        assert jogo.conquistas_obtidas == 31

def test_importacao_steam_faz_rollback_se_item_posterior_for_invalido(app):
    from app.models import Jogo

    with app.app_context():
        usuario = _criar_usuario()
        servico = BacklogService(usuario)

        with pytest.raises(ErroDeValidacao):
            servico.importar_jogos_steam(
                [
                    {"steam_appid": 1, "titulo": "Válido", "tempo_jogado_horas": 3},
                    {"steam_appid": 2, "titulo": "", "tempo_jogado_horas": 1},
                ]
            )

        assert Jogo.query.filter_by(usuario_id=usuario.id).count() == 0
