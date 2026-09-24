from datetime import datetime, timezone

from app.extensions import db
from app.models.categoria import jogo_categoria

STATUS_VALIDOS = ("quero_jogar", "jogando", "jogado", "zerado", "platinado", "abandonado")
PRIORIDADES_VALIDAS = ("baixa", "normal", "alta")


class Jogo(db.Model):
    __tablename__ = "jogo"
    __table_args__ = (
        db.CheckConstraint(f"status IN {STATUS_VALIDOS}", name="ck_jogo_status_valido"),
        db.CheckConstraint(f"prioridade IN {PRIORIDADES_VALIDAS}", name="ck_jogo_prioridade_valida"),
        db.CheckConstraint("nota IS NULL OR (nota >= 0 AND nota <= 10)", name="ck_jogo_nota_intervalo"),
        db.CheckConstraint("tempo_jogado_horas >= 0", name="ck_jogo_tempo_nao_negativo"),
        db.CheckConstraint("total_conquistas >= 0", name="ck_jogo_total_conquistas_nao_negativo"),
        db.CheckConstraint("conquistas_obtidas >= 0", name="ck_jogo_conquistas_obtidas_nao_negativo"),
        db.CheckConstraint("conquistas_obtidas <= total_conquistas", name="ck_jogo_conquistas_consistentes"),
        db.UniqueConstraint("usuario_id", "steam_appid", name="uq_jogo_usuario_steam_appid"),
        db.Index("ix_jogo_status", "status"),
        db.Index("ix_jogo_prioridade", "prioridade"),
        db.Index("ix_jogo_steam_appid", "steam_appid"),
        db.Index("ix_jogo_criado_em", "criado_em"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, index=True)

    titulo = db.Column(db.String(160), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="quero_jogar")
    nota = db.Column(db.Float, nullable=True)
    favorito = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    prioridade = db.Column(db.String(10), nullable=False, default="normal", server_default="normal")

    tempo_jogado_horas = db.Column(db.Integer, nullable=False, default=0)
    total_conquistas = db.Column(db.Integer, nullable=False, default=0)
    conquistas_obtidas = db.Column(db.Integer, nullable=False, default=0)

    steam_appid = db.Column(db.Integer, nullable=True)
    capa_url = db.Column(db.String(500), nullable=True)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=db.func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    categorias = db.relationship(
        "Categoria", secondary=jogo_categoria, backref=db.backref("jogos", lazy="dynamic")
    )
    runs = db.relationship("RunDiario", backref="jogo", cascade="all, delete-orphan", lazy="dynamic")
    builds = db.relationship("BuildAnotacao", backref="jogo", cascade="all, delete-orphan", lazy="dynamic")
    conquistas_steam = db.relationship(
        "ConquistaSteam",
        backref="jogo",
        cascade="all, delete-orphan",
    )
    historico = db.relationship(
        "HistoricoJogo",
        backref="jogo",
        cascade="all, delete-orphan",
    )
    desafios = db.relationship("Desafio", back_populates="jogo", cascade="all, delete-orphan")

    @property
    def percentual_conquistas(self):
        if not self.total_conquistas:
            return 0
        return round((self.conquistas_obtidas / self.total_conquistas) * 100)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "status": self.status,
            "nota": self.nota,
            "favorito": self.favorito,
            "prioridade": self.prioridade,
            "tempo_jogado_horas": self.tempo_jogado_horas,
            "total_conquistas": self.total_conquistas,
            "conquistas_obtidas": self.conquistas_obtidas,
            "percentual_conquistas": self.percentual_conquistas,
            "categorias": [c.nome for c in self.categorias],
            "steam_appid": self.steam_appid,
            "capa_url": self.capa_url,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }

    def __repr__(self):
        return f"<Jogo {self.titulo!r}>"
