from app.extensions import db

# Tabela associativa pura (sem colunas extras) para o relacionamento N:M
jogo_categoria = db.Table(
    "jogo_categoria",
    db.Column("jogo_id", db.Integer, db.ForeignKey("jogo.id", ondelete="CASCADE"), primary_key=True),
    db.Column("categoria_id", db.Integer, db.ForeignKey("categoria.id", ondelete="CASCADE"), primary_key=True),
)


class Categoria(db.Model):
    __tablename__ = "categoria"
    __table_args__ = (
        db.UniqueConstraint("usuario_id", "nome", name="uq_categoria_usuario_nome"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    nome = db.Column(db.String(60), nullable=False)
    cor_hex = db.Column(db.String(7), nullable=False, default="#a78bfa")

    def __repr__(self):
        return f"<Categoria {self.nome}>"
