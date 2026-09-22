def _criar_jogo(client):
    resposta = client.post(
        "/api/jogos",
        json={"titulo": "Hades", "status": "jogando"},
    )
    assert resposta.status_code == 201
    return resposta.get_json()["id"]


def test_crud_completo_de_run(client_autenticado):
    jogo_id = _criar_jogo(client_autenticado)

    criada = client_autenticado.post(
        "/api/runs",
        json={
            "jogo_id": jogo_id,
            "data": "2026-09-08",
            "tempo_duracao": "00:12:30",
            "resultado": "derrota",
            "causa_morte": "Chefe final",
        },
    )
    assert criada.status_code == 201
    run_id = criada.get_json()["id"]

    obtida = client_autenticado.get(f"/api/runs/{run_id}")
    assert obtida.status_code == 200
    assert obtida.get_json()["tempo_duracao"] == "00:12:30"

    atualizada = client_autenticado.put(
        f"/api/runs/{run_id}",
        json={
            "jogo_id": jogo_id,
            "data": "2026-09-09",
            "tempo_duracao": "00:10:00",
            "resultado": "vitoria",
            "causa_morte": "deve ser descartada",
        },
    )
    assert atualizada.status_code == 200
    corpo = atualizada.get_json()
    assert corpo["resultado"] == "vitoria"
    assert corpo["causa_morte"] is None
    assert corpo["data"] == "2026-09-09"

    excluida = client_autenticado.delete(f"/api/runs/{run_id}")
    assert excluida.status_code == 204
    assert client_autenticado.get(f"/api/runs/{run_id}").status_code == 404


def test_run_com_duracao_invalida_retorna_400(client_autenticado):
    jogo_id = _criar_jogo(client_autenticado)
    resposta = client_autenticado.post(
        "/api/runs",
        json={
            "jogo_id": jogo_id,
            "tempo_duracao": "01:99:00",
            "resultado": "vitoria",
        },
    )
    assert resposta.status_code == 400
    assert "Tempo de duração inválido" in resposta.get_json()["erro"]


def test_crud_completo_de_build(client_autenticado):
    jogo_id = _criar_jogo(client_autenticado)

    criada = client_autenticado.post(
        "/api/builds",
        json={
            "jogo_id": jogo_id,
            "nome_build": "Escudo",
            "detalhes_equipamento": "Armadura pesada",
            "habilidades": "Defesa",
        },
    )
    assert criada.status_code == 201
    build_id = criada.get_json()["id"]

    obtida = client_autenticado.get(f"/api/builds/{build_id}")
    assert obtida.status_code == 200
    assert obtida.get_json()["nome_build"] == "Escudo"

    atualizada = client_autenticado.put(
        f"/api/builds/{build_id}",
        json={
            "jogo_id": jogo_id,
            "nome_build": "Escudo + Força",
            "detalhes_equipamento": "Armadura pesada + espada",
            "habilidades": "Defesa e força",
        },
    )
    assert atualizada.status_code == 200
    assert atualizada.get_json()["nome_build"] == "Escudo + Força"

    excluida = client_autenticado.delete(f"/api/builds/{build_id}")
    assert excluida.status_code == 204
    assert client_autenticado.get(f"/api/builds/{build_id}").status_code == 404


def test_build_sem_nome_retorna_400(client_autenticado):
    jogo_id = _criar_jogo(client_autenticado)
    resposta = client_autenticado.post(
        "/api/builds",
        json={"jogo_id": jogo_id, "nome_build": ""},
    )
    assert resposta.status_code == 400


def test_run_sem_data_retorna_400(client_autenticado):
    jogo_id = _criar_jogo(client_autenticado)
    resposta = client_autenticado.post(
        "/api/runs",
        json={
            "jogo_id": jogo_id,
            "data": "",
            "tempo_duracao": "00:10:00",
            "resultado": "vitoria",
        },
    )
    assert resposta.status_code == 400
    assert "data da run" in resposta.get_json()["erro"].lower()


def test_run_com_duracao_zero_retorna_400(client_autenticado):
    jogo_id = _criar_jogo(client_autenticado)
    resposta = client_autenticado.post(
        "/api/runs",
        json={
            "jogo_id": jogo_id,
            "data": "2026-09-08",
            "tempo_duracao": "00:00:00",
            "resultado": "vitoria",
        },
    )
    assert resposta.status_code == 400


def test_run_com_mais_de_24_horas_e_aceita(client_autenticado):
    jogo_id = _criar_jogo(client_autenticado)
    resposta = client_autenticado.post(
        "/api/runs",
        json={
            "jogo_id": jogo_id,
            "data": "2026-09-08",
            "tempo_duracao": "25:10:05",
            "resultado": "vitoria",
        },
    )
    assert resposta.status_code == 201
    assert resposta.get_json()["tempo_duracao"] == "25:10:05"


def test_excluir_jogo_remove_runs_e_builds_associados(client_autenticado):
    jogo_id = _criar_jogo(client_autenticado)

    run = client_autenticado.post(
        "/api/runs",
        json={
            "jogo_id": jogo_id,
            "data": "2026-09-08",
            "tempo_duracao": "00:12:30",
            "resultado": "vitoria",
        },
    )
    build = client_autenticado.post(
        "/api/builds",
        json={"jogo_id": jogo_id, "nome_build": "Teste"},
    )
    assert run.status_code == 201
    assert build.status_code == 201

    excluido = client_autenticado.delete(f"/api/jogos/{jogo_id}")
    assert excluido.status_code == 204
    assert client_autenticado.get("/api/runs").get_json() == []
    assert client_autenticado.get("/api/builds").get_json() == []
