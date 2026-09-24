from datetime import datetime, timezone

from app.extensions import db


class HistoricoJogo(db.Model):
    __tablename__ = "historico_jogo"
    __table_args__ = (db.Index("ix_historico_jogo_jogo_criado", "jogo_id", "criado_em"),)

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogo.id", ondelete="CASCADE"), nullable=False)
    tipo = db.Column(db.String(40), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), server_default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "jogo_id": self.jogo_id,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }
