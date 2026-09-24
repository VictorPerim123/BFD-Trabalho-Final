from app.extensions import db
from app.models import ConquistaSteam, HistoricoJogo, Jogo, RunDiario, Usuario
from app.services.backlog_service import BacklogService


def _usuario(username="jornada"):
    usuario = Usuario(
        nome="Jogador Jornada",
        username=username,
        email=f"{username}@savepoint.dev",
    )
    usuario.set_senha("SenhaForte123")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def test_conquistas_detalhadas_sao_persistidas_e_atualizadas_sem_duplicar(app):
    with app.app_context():
        servico = BacklogService(_usuario())
        servico.importar_jogos_steam(
            [
                {
                    "steam_appid": 10,
                    "titulo": "Jogo Steam",
                    "tempo_jogado_horas": 5,
                    "total_conquistas": 2,
                    "conquistas_obtidas": 1,
                    "conquistas_sincronizadas": True,
                    "conquistas_disponiveis": True,
                    "conquistas_detalhes": [
                        {
                            "api_name": "ACH_A",
                            "nome": "Primeira",
                            "descricao": "Faça algo",
                            "desbloqueada": True,
                            "unlocktime": 1700000000,
                        },
                        {
                            "api_name": "ACH_B",
                            "nome": "Segunda",
                            "desbloqueada": False,
                        },
                    ],
                }
            ]
        )

        jogo = Jogo.query.filter_by(steam_appid=10).one()
        assert ConquistaSteam.query.filter_by(jogo_id=jogo.id).count() == 2
        primeira = ConquistaSteam.query.filter_by(jogo_id=jogo.id, api_name="ACH_A").one()
        assert primeira.desbloqueada is True
        assert primeira.desbloqueada_em is not None

        servico.importar_jogos_steam(
            [
                {
                    "steam_appid": 10,
                    "titulo": "Jogo Steam",
                    "tempo_jogado_horas": 5,
                    "total_conquistas": 2,
                    "conquistas_obtidas": 2,
                    "conquistas_sincronizadas": True,
                    "conquistas_disponiveis": True,
                    "conquistas_detalhes": [
                        {
                            "api_name": "ACH_A",
                            "nome": "Primeira",
                            "descricao": "Faça algo",
                            "desbloqueada": True,
                        },
                        {
                            "api_name": "ACH_B",
                            "nome": "Segunda",
                            "desbloqueada": True,
                            "unlocktime": 1700000100,
                        },
                    ],
                }
            ]
        )

        assert ConquistaSteam.query.filter_by(jogo_id=jogo.id).count() == 2
        primeira_atualizada = ConquistaSteam.query.filter_by(jogo_id=jogo.id, api_name="ACH_A").one()
        segunda = ConquistaSteam.query.filter_by(jogo_id=jogo.id, api_name="ACH_B").one()
        assert primeira_atualizada.desbloqueada_em == primeira.desbloqueada_em
        assert segunda.desbloqueada is True
        assert segunda.desbloqueada_em is not None


def test_falha_de_conquistas_nao_apaga_detalhes_anteriores(app):
    with app.app_context():
        servico = BacklogService(_usuario("jornadafalha"))
        servico.importar_jogos_steam(
            [
                {
                    "steam_appid": 20,
                    "titulo": "Com conquistas",
                    "tempo_jogado_horas": 1,
                    "total_conquistas": 1,
                    "conquistas_obtidas": 1,
                    "conquistas_sincronizadas": True,
                    "conquistas_disponiveis": True,
                    "conquistas_detalhes": [
                        {"api_name": "ACH", "nome": "A", "desbloqueada": True}
                    ],
                }
            ]
        )
        jogo = Jogo.query.filter_by(steam_appid=20).one()

        servico.importar_jogos_steam(
            [
                {
                    "steam_appid": 20,
                    "titulo": "Com conquistas",
                    "tempo_jogado_horas": 1,
                    "total_conquistas": 0,
                    "conquistas_obtidas": 0,
                    "conquistas_sincronizadas": False,
                    "conquistas_detalhes": [],
                }
            ]
        )

        assert jogo.total_conquistas == 1
        assert jogo.conquistas_obtidas == 1
        assert ConquistaSteam.query.filter_by(jogo_id=jogo.id).count() == 1


def test_quase_concluidos_respeita_intervalo_de_70_a_99_porcento(app):
    with app.app_context():
        servico = BacklogService(_usuario("quase"))
        for titulo, obtidas, total in (
            ("Sessenta e nove", 69, 100),
            ("Arredondaria para setenta", 69, 99),
            ("Setenta", 70, 100),
            ("Noventa e nove", 99, 100),
            ("Cem", 100, 100),
        ):
            servico.criar_jogo(
                {"titulo": titulo, "total_conquistas": total, "conquistas_obtidas": obtidas}
            )

        stats = servico.calcular_estatisticas_dashboard()
        titulos = {item["titulo"] for item in stats["quase_concluidos"]}
        assert titulos == {"Setenta", "Noventa e nove"}
        assert stats["saude"]["quase_concluidos"] == 2


def test_build_aceita_atributos_flexiveis(app):
    with app.app_context():
        servico = BacklogService(_usuario("buildflex"))
        jogo = servico.criar_jogo({"titulo": "RPG"})
        build = servico.registrar_build(
            {
                "jogo_id": jogo.id,
                "nome_build": "Bleed",
                "objetivo": "Bosses",
                "status": "em_uso",
                "nivel": 125,
                "atributos": [
                    {"nome": "Força", "valor": "20"},
                    {"nome": "Arcano", "valor": "60"},
                ],
            }
        )

        assert build.status == "em_uso"
        assert build.nivel == 125
        assert [(item.nome, item.valor) for item in build.atributos] == [
            ("Força", "20"),
            ("Arcano", "60"),
        ]


def test_runs_detectam_pb_por_jogo_e_categoria_e_aceitam_build(app):
    with app.app_context():
        servico = BacklogService(_usuario("speedrun"))
        jogo = servico.criar_jogo({"titulo": "Celeste"})
        build = servico.registrar_build({"jogo_id": jogo.id, "nome_build": "Any%"})

        primeira = servico.registrar_run(
            {
                "jogo_id": jogo.id,
                "build_id": build.id,
                "data": "2026-09-20",
                "tempo_duracao": "00:50:00",
                "resultado": "vitoria",
                "categoria": "Any%",
            }
        )
        segunda = servico.registrar_run(
            {
                "jogo_id": jogo.id,
                "build_id": build.id,
                "data": "2026-09-21",
                "tempo_duracao": "00:45:00",
                "resultado": "vitoria",
                "categoria": "Any%",
            }
        )
        derrota = servico.registrar_run(
            {
                "jogo_id": jogo.id,
                "data": "2026-09-22",
                "tempo_duracao": "00:40:00",
                "resultado": "derrota",
                "categoria": "Any%",
            }
        )

        db.session.refresh(primeira)
        db.session.refresh(segunda)
        db.session.refresh(derrota)
        assert primeira.eh_pb is False
        assert segunda.eh_pb is True
        assert segunda.build_id == build.id
        assert derrota.eh_pb is False
        assert RunDiario.query.filter_by(jogo_id=jogo.id, categoria="Any%", eh_pb=True).count() == 1


def test_desafio_concluido_e_acoes_relevantes_geram_historico(app):
    with app.app_context():
        servico = BacklogService(_usuario("historico"))
        jogo = servico.criar_jogo({"titulo": "Hades"})
        servico.registrar_build({"jogo_id": jogo.id, "nome_build": "Escudo"})
        desafio = servico.registrar_desafio(
            {
                "jogo_id": jogo.id,
                "titulo": "Finalizar com escudo",
                "tipo": "personalizado",
                "meta": "1 vitória",
            }
        )
        servico.atualizar_desafio(
            desafio.id,
            {
                "jogo_id": jogo.id,
                "titulo": desafio.titulo,
                "tipo": desafio.tipo,
                "meta": desafio.meta,
                "status": "concluido",
                "data_inicio": desafio.data_inicio.isoformat(),
            },
        )

        tipos = {
            item.tipo for item in HistoricoJogo.query.filter_by(jogo_id=jogo.id).all()
        }
        assert "ADICIONADO" in tipos
        assert "BUILD_CRIADA" in tipos
        assert "DESAFIO_CONCLUIDO" in tipos


def test_api_desafios_respeita_ownership(client_autenticado, app):
    jogo = client_autenticado.post("/api/jogos", json={"titulo": "Meu jogo"}).get_json()
    criada = client_autenticado.post(
        "/api/desafios",
        json={"titulo": "Minha meta", "jogo_id": jogo["id"], "tipo": "backlog"},
    )
    assert criada.status_code == 201
    assert criada.get_json()["titulo"] == "Minha meta"

    with app.app_context():
        outro = Usuario(nome="Outro", username="outroch", email="outroch@savepoint.dev")
        outro.set_senha("SenhaForte123")
        db.session.add(outro)
        db.session.commit()
        outro_jogo = Jogo(usuario_id=outro.id, titulo="Privado")
        db.session.add(outro_jogo)
        db.session.commit()
        outro_servico = BacklogService(outro)
        privado = outro_servico.registrar_desafio(
            {"titulo": "Privado", "jogo_id": outro_jogo.id}
        )
        privado_id = privado.id

    assert client_autenticado.get(f"/api/desafios/{privado_id}").status_code == 404


def test_dashboard_considera_apenas_dados_do_usuario(app):
    with app.app_context():
        usuario = _usuario("dashboardowner")
        outro = _usuario("dashboardoutro")
        servico = BacklogService(usuario)
        outro_servico = BacklogService(outro)
        servico.criar_jogo({"titulo": "Meu jogo", "tempo_jogado_horas": 10, "favorito": True})
        outro_servico.criar_jogo({"titulo": "Jogo alheio", "tempo_jogado_horas": 99, "favorito": True})

        stats = servico.calcular_estatisticas_dashboard()

        assert stats["total_jogos"] == 1
        assert stats["horas_totais"] == 10
        assert stats["favoritos"] == 1


def test_jornada_usa_modais_para_build_e_run(client_autenticado):
    html = client_autenticado.get("/jornada").get_data(as_text=True)

    assert '<dialog class="app-modal app-modal--wide" id="build-form-card"' in html
    assert '<dialog class="app-modal" id="run-form-card"' in html
    assert "+ Nova build" in html
    assert "+ Registrar run" in html
