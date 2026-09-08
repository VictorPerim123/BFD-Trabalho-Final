from app.extensions import db


class BuildAnotacao(db.Model):
    __tablename__ = "build_anotacao"

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogo.id", ondelete="CASCADE"), nullable=False, index=True)

    nome_build = db.Column(db.String(120), nullable=False)
    detalhes_equipamento = db.Column(db.Text, nullable=True)
    habilidades = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "jogo_id": self.jogo_id,
            "nome_build": self.nome_build,
            "detalhes_equipamento": self.detalhes_equipamento,
            "habilidades": self.habilidades,
        }
