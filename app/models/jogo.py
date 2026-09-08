from datetime import datetime, timezone

from app.extensions import db
from app.models.categoria import jogo_categoria

STATUS_VALIDOS = ("quero_jogar", "jogando", "zerado", "platinado", "abandonado")


class Jogo(db.Model):
    __tablename__ = "jogo"
    __table_args__ = (
        db.CheckConstraint(f"status IN {STATUS_VALIDOS}", name="ck_jogo_status_valido"),
        db.CheckConstraint("nota IS NULL OR (nota >= 0 AND nota <= 10)", name="ck_jogo_nota_intervalo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, index=True)

    titulo = db.Column(db.String(160), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="quero_jogar")
    nota = db.Column(db.Float, nullable=True)

    tempo_jogado_horas = db.Column(db.Integer, nullable=False, default=0)
    total_conquistas = db.Column(db.Integer, nullable=False, default=0)
    conquistas_obtidas = db.Column(db.Integer, nullable=False, default=0)

    steam_appid = db.Column(db.Integer, nullable=True)  # preenchido quando importado da Steam
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    categorias = db.relationship(
        "Categoria", secondary=jogo_categoria, backref=db.backref("jogos", lazy="dynamic")
    )
    runs = db.relationship("RunDiario", backref="jogo", cascade="all, delete-orphan", lazy="dynamic")
    builds = db.relationship("BuildAnotacao", backref="jogo", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def percentual_conquistas(self):
        """Percentual de conquistas obtidas (0 quando o jogo não rastreia conquistas)."""
        if not self.total_conquistas:
            return 0
        return round((self.conquistas_obtidas / self.total_conquistas) * 100)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "status": self.status,
            "nota": self.nota,
            "tempo_jogado_horas": self.tempo_jogado_horas,
            "total_conquistas": self.total_conquistas,
            "conquistas_obtidas": self.conquistas_obtidas,
            "percentual_conquistas": self.percentual_conquistas,
            "categorias": [c.nome for c in self.categorias],
            "steam_appid": self.steam_appid,
        }

    def __repr__(self):
        return f"<Jogo {self.titulo!r}>"
