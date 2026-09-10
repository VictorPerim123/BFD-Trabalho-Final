def test_api_jogos_sem_login_retorna_401(client):
    resposta = client.get("/api/jogos")
    assert resposta.status_code == 401


def test_criar_e_listar_jogo_via_api_autenticada(client_autenticado):
    resposta_post = client_autenticado.post(
        "/api/jogos",
        json={"titulo": "Hollow Knight", "status": "jogando", "categorias": ["Metroidvania"]},
    )
    assert resposta_post.status_code == 201
    jogo_criado = resposta_post.get_json()
    assert jogo_criado["titulo"] == "Hollow Knight"
    assert jogo_criado["categorias"] == ["Metroidvania"]

    resposta_get = client_autenticado.get("/api/jogos")
    assert resposta_get.status_code == 200
    titulos = [jogo["titulo"] for jogo in resposta_get.get_json()]
    assert "Hollow Knight" in titulos


def test_criar_jogo_sem_titulo_retorna_400(client_autenticado):
    resposta = client_autenticado.post("/api/jogos", json={"titulo": ""})
    assert resposta.status_code == 400
    assert "erro" in resposta.get_json()


def test_excluir_jogo_de_outro_usuario_retorna_404(client_autenticado, app):
    from app.extensions import db
    from app.models import Usuario, Jogo

    with app.app_context():
        outro = Usuario(nome="Outro", username="outro", email="outro@savepoint.dev")
        outro.set_senha("SenhaForte123")
        db.session.add(outro)
        db.session.commit()

        jogo_do_outro = Jogo(usuario_id=outro.id, titulo="Jogo Privado")
        db.session.add(jogo_do_outro)
        db.session.commit()
        jogo_id = jogo_do_outro.id

    resposta = client_autenticado.delete(f"/api/jogos/{jogo_id}")
    assert resposta.status_code == 404
