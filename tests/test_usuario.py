from app.models import Usuario


def test_senha_e_armazenada_como_hash_e_nao_em_texto_plano(app):
    usuario = Usuario(nome="Ana", username="ana", email="ana@savepoint.dev")
    usuario.set_senha("MinhaSenh@123")

    assert usuario.senha_hash != "MinhaSenh@123"
    assert "MinhaSenh@123" not in usuario.senha_hash


def test_verificar_senha_aceita_a_senha_correta(app):
    usuario = Usuario(nome="Ana", username="ana", email="ana@savepoint.dev")
    usuario.set_senha("MinhaSenh@123")

    assert usuario.verificar_senha("MinhaSenh@123") is True


def test_verificar_senha_rejeita_senha_incorreta(app):
    usuario = Usuario(nome="Ana", username="ana", email="ana@savepoint.dev")
    usuario.set_senha("MinhaSenh@123")

    assert usuario.verificar_senha("senha-errada") is False
