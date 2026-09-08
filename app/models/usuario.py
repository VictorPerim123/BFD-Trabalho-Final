from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(60), unique=True, nullable=False, index=True)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    steam_id = db.Column(db.String(32), nullable=True)  # opcional, usado na importação Steam
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    jogos = db.relationship("Jogo", backref="usuario", cascade="all, delete-orphan", lazy="dynamic")
    categorias = db.relationship("Categoria", backref="usuario", cascade="all, delete-orphan", lazy="dynamic")

    def set_senha(self, senha_texto_plano):
        self.senha_hash = generate_password_hash(senha_texto_plano)

    def verificar_senha(self, senha_texto_plano):
        return check_password_hash(self.senha_hash, senha_texto_plano)

    def __repr__(self):
        return f"<Usuario {self.username}>"
