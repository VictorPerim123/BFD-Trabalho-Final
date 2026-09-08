from app.extensions import db

STATUS_SOLICITACAO_VALIDOS = ("pendente", "aceita", "recusada")


class Amizade(db.Model):
    __tablename__ = "amizade"
    __table_args__ = (
        db.CheckConstraint(
            f"status_solicitacao IN {STATUS_SOLICITACAO_VALIDOS}", name="ck_amizade_status_valido"
        ),
    )

    usuario_solicitante_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True
    )
    usuario_receptor_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True
    )
    status_solicitacao = db.Column(db.String(10), nullable=False, default="pendente")

    solicitante = db.relationship("Usuario", foreign_keys=[usuario_solicitante_id])
    receptor = db.relationship("Usuario", foreign_keys=[usuario_receptor_id])
