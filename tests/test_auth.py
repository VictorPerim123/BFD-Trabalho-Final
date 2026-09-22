from app.models import Usuario


def _dados_validos(**alteracoes):
    dados = {
        "nome": "Nova Pessoa",
        "username": "novapessoa",
        "email": "nova@savepoint.dev",
        "senha": "Senha123",
    }
    dados.update(alteracoes)
    return dados


def test_cadastro_com_email_invalido_retorna_mensagem(client, app):
    resposta = client.post("/registrar", data=_dados_validos(email="email-invalido"))

    assert resposta.status_code == 200
    assert "Informe um e-mail válido" in resposta.get_data(as_text=True)
    with app.app_context():
        assert Usuario.query.count() == 0


def test_cadastro_rejeita_campos_acima_do_limite(client, app):
    resposta = client.post("/registrar", data=_dados_validos(username="u" * 61))

    assert resposta.status_code == 200
    assert "no máximo 60 caracteres" in resposta.get_data(as_text=True)
    with app.app_context():
        assert Usuario.query.count() == 0


def test_cadastro_valido_cria_usuario_e_autentica(client, app):
    resposta = client.post("/registrar", data=_dados_validos(), follow_redirects=False)

    assert resposta.status_code == 302
    with app.app_context():
        usuario = Usuario.query.filter_by(username="novapessoa").one()
        assert usuario.email == "nova@savepoint.dev"

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200


def test_formulario_de_cadastro_publica_limites_html(client):
    html = client.get("/registrar").get_data(as_text=True)

    assert 'name="nome" maxlength="120"' in html
    assert 'name="username" maxlength="60"' in html
    assert 'name="email" maxlength="160"' in html


def test_logout_exibe_feedback_na_tela_de_login(client_autenticado):
    resposta = client_autenticado.post("/logout", follow_redirects=True)

    assert resposta.status_code == 200
    assert "Você saiu da sua conta." in resposta.get_data(as_text=True)
