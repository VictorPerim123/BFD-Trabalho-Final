from app.extensions import db

STATUS_BUILD_VALIDOS = ("planejada", "em_uso", "finalizada", "experimental")


class BuildAnotacao(db.Model):
    __tablename__ = "build_anotacao"
    __table_args__ = (
        db.CheckConstraint(f"status IN {STATUS_BUILD_VALIDOS}", name="ck_build_status_valido"),
    )

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogo.id", ondelete="CASCADE"), nullable=False, index=True)

    nome_build = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    objetivo = db.Column(db.String(160), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="planejada", server_default="planejada")
    nivel = db.Column(db.Integer, nullable=True)
    detalhes_equipamento = db.Column(db.Text, nullable=True)
    habilidades = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    atributos = db.relationship(
        "BuildAtributo",
        back_populates="build",
        cascade="all, delete-orphan",
        order_by="BuildAtributo.ordem, BuildAtributo.id",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "jogo_id": self.jogo_id,
            "nome_build": self.nome_build,
            "descricao": self.descricao,
            "objetivo": self.objetivo,
            "status": self.status,
            "nivel": self.nivel,
            "detalhes_equipamento": self.detalhes_equipamento,
            "habilidades": self.habilidades,
            "observacoes": self.observacoes,
            "atributos": [atributo.to_dict() for atributo in self.atributos],
        }


class BuildAtributo(db.Model):
    __tablename__ = "build_atributo"
    __table_args__ = (
        db.UniqueConstraint("build_id", "nome", name="uq_build_atributo_nome"),
        db.Index("ix_build_atributo_build_id", "build_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    build_id = db.Column(db.Integer, db.ForeignKey("build_anotacao.id", ondelete="CASCADE"), nullable=False)
    nome = db.Column(db.String(80), nullable=False)
    valor = db.Column(db.String(120), nullable=False)
    ordem = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    build = db.relationship("BuildAnotacao", back_populates="atributos")

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "valor": self.valor, "ordem": self.ordem}
