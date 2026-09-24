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


def test_login_nao_redireciona_para_site_externo(client, usuario):
    resposta = client.post(
        "/login?proximo=https://exemplo-malicioso.invalid",
        data={"usuario": "jogadorteste", "senha": "SenhaForte123"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")
    assert "exemplo-malicioso.invalid" not in resposta.headers["Location"]

def test_cadastro_rejeita_senha_curta(client, app):
    resposta = client.post("/registrar", data=_dados_validos(senha="1234567"))

    assert resposta.status_code == 200
    assert "ao menos 8 caracteres" in resposta.get_data(as_text=True)
    with app.app_context():
        assert Usuario.query.count() == 0


def test_login_nao_redireciona_com_barra_invertida(client, usuario):
    resposta = client.post(
        "/login?proximo=/%5C%5Cexemplo-malicioso.invalid",
        data={"usuario": "jogadorteste", "senha": "SenhaForte123"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")
    assert "exemplo-malicioso.invalid" not in resposta.headers["Location"]


def test_respostas_incluem_cabecalhos_de_seguranca(client):
    resposta = client.get("/login")

    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert resposta.headers["X-Frame-Options"] == "DENY"
    assert resposta.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_perfil_exige_autenticacao(client):
    resposta = client.get("/perfil", follow_redirects=False)

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]



def test_perfil_renderiza_para_usuario_autenticado(client_autenticado):
    resposta = client_autenticado.get("/perfil")

    assert resposta.status_code == 200
    conteudo = resposta.get_data(as_text=True)
    assert "Meu perfil" in conteudo
    assert "jogadorteste" in conteudo
    assert "teste@savepoint.dev" in conteudo

def test_perfil_atualiza_dados_do_usuario(client_autenticado, app, usuario):
    resposta = client_autenticado.post(
        "/perfil",
        data={
            "acao": "dados",
            "nome": "Jogador Atualizado",
            "username": "jogadornovo",
            "email": "novo@savepoint.dev",
            "steam_id": "76561197960287930",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    with app.app_context():
        atualizado = Usuario.query.get(usuario.id)
        assert atualizado.nome == "Jogador Atualizado"
        assert atualizado.username == "jogadornovo"
        assert atualizado.email == "novo@savepoint.dev"
        assert atualizado.steam_id == "76561197960287930"


def test_perfil_rejeita_username_ou_email_duplicado(client_autenticado, app):
    with app.app_context():
        outro = Usuario(nome="Outro", username="outro", email="outro@savepoint.dev")
        outro.set_senha("SenhaForte123")
        from app.extensions import db
        db.session.add(outro)
        db.session.commit()

    resposta = client_autenticado.post(
        "/perfil",
        data={
            "acao": "dados",
            "nome": "Jogador",
            "username": "outro",
            "email": "jogador@savepoint.dev",
            "steam_id": "",
        },
    )

    assert resposta.status_code == 200
    assert "Já existe uma conta" in resposta.get_data(as_text=True)


def test_perfil_altera_senha_com_confirmacao_da_atual(client_autenticado, app, usuario):
    resposta = client_autenticado.post(
        "/perfil",
        data={
            "acao": "senha",
            "senha_atual": "SenhaForte123",
            "nova_senha": "NovaSenha456",
            "confirmar_senha": "NovaSenha456",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    with app.app_context():
        atualizado = Usuario.query.get(usuario.id)
        assert atualizado.verificar_senha("NovaSenha456") is True


def test_perfil_rejeita_senha_atual_incorreta(client_autenticado):
    resposta = client_autenticado.post(
        "/perfil",
        data={
            "acao": "senha",
            "senha_atual": "Errada123",
            "nova_senha": "NovaSenha456",
            "confirmar_senha": "NovaSenha456",
        },
    )

    assert resposta.status_code == 200
    assert "senha atual está incorreta" in resposta.get_data(as_text=True)
