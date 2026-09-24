from datetime import date as date_cls, datetime, timezone

from app.extensions import db

STATUS_DESAFIO_VALIDOS = ("ativo", "concluido", "cancelado")
TIPOS_DESAFIO_VALIDOS = ("backlog", "conquistas", "speedrun", "personalizado")


class Desafio(db.Model):
    __tablename__ = "desafio"
    __table_args__ = (
        db.CheckConstraint(f"status IN {STATUS_DESAFIO_VALIDOS}", name="ck_desafio_status_valido"),
        db.CheckConstraint(f"tipo IN {TIPOS_DESAFIO_VALIDOS}", name="ck_desafio_tipo_valido"),
        db.Index("ix_desafio_usuario_status", "usuario_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogo.id", ondelete="CASCADE"), nullable=True)
    titulo = db.Column(db.String(160), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(30), nullable=False, default="personalizado", server_default="personalizado")
    meta = db.Column(db.String(120), nullable=True)
    progresso = db.Column(db.String(120), nullable=True)
    data_inicio = db.Column(db.Date, nullable=False, default=date_cls.today, server_default=db.func.current_date())
    data_limite = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="ativo", server_default="ativo")
    criado_em = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), server_default=db.func.now())
    atualizado_em = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), server_default=db.func.now(), onupdate=lambda: datetime.now(timezone.utc))

    jogo = db.relationship("Jogo", back_populates="desafios")

    def to_dict(self):
        return {
            "id": self.id,
            "jogo_id": self.jogo_id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "tipo": self.tipo,
            "meta": self.meta,
            "progresso": self.progresso,
            "data_inicio": self.data_inicio.isoformat() if self.data_inicio else None,
            "data_limite": self.data_limite.isoformat() if self.data_limite else None,
            "status": self.status,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }
