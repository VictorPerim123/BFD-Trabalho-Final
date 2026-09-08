import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Usuario


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def usuario(app):
    with app.app_context():
        u = Usuario(nome="Jogador Teste", username="jogadorteste", email="teste@savepoint.dev")
        u.set_senha("SenhaForte123")
        db.session.add(u)
        db.session.commit()
        db.session.refresh(u)
        return u


@pytest.fixture()
def client_autenticado(client, usuario):
    """Cliente de teste já com sessão de login ativa."""
    client.post("/login", data={"usuario": "jogadorteste", "senha": "SenhaForte123"})
    return client
