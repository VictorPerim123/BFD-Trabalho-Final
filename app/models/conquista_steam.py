from datetime import datetime, timezone

from app.extensions import db


class ConquistaSteam(db.Model):
    __tablename__ = "conquista_steam"
    __table_args__ = (
        db.UniqueConstraint("jogo_id", "api_name", name="uq_conquista_jogo_api_name"),
        db.Index("ix_conquista_steam_jogo_id", "jogo_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogo.id", ondelete="CASCADE"), nullable=False)
    api_name = db.Column(db.String(160), nullable=False)
    nome = db.Column(db.String(200), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    icone_url = db.Column(db.String(500), nullable=True)
    icone_bloqueada_url = db.Column(db.String(500), nullable=True)
    desbloqueada = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    desbloqueada_em = db.Column(db.DateTime, nullable=True)

    @classmethod
    def data_unlock(cls, valor):
        try:
            timestamp = int(valor or 0)
        except (TypeError, ValueError, OverflowError, OSError):
            return None
        if timestamp <= 0:
            return None
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)

    def to_dict(self):
        return {
            "id": self.id,
            "api_name": self.api_name,
            "nome": self.nome or self.api_name,
            "descricao": self.descricao,
            "icone_url": self.icone_url,
            "icone_bloqueada_url": self.icone_bloqueada_url,
            "desbloqueada": self.desbloqueada,
            "desbloqueada_em": self.desbloqueada_em.isoformat() if self.desbloqueada_em else None,
        }
