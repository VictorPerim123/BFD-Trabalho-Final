from datetime import date as date_cls

from app.extensions import db

RESULTADOS_VALIDOS = ("vitoria", "derrota")


class RunDiario(db.Model):
    __tablename__ = "run_diario"
    __table_args__ = (
        db.CheckConstraint(f"resultado IN {RESULTADOS_VALIDOS}", name="ck_run_resultado_valido"),
    )

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogo.id", ondelete="CASCADE"), nullable=False, index=True)

    data = db.Column(db.Date, nullable=False, default=date_cls.today)
    duracao_segundos = db.Column(db.Integer, nullable=False, default=0)
    resultado = db.Column(db.String(10), nullable=False)
    causa_morte = db.Column(db.String(200), nullable=True)

    @property
    def tempo_formatado(self):
        h, resto = divmod(self.duracao_segundos, 3600)
        m, s = divmod(resto, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def segundos_a_partir_de_hhmmss(texto):
        """Converte 'HH:MM:SS' (ou 'MM:SS') vindo do <input type=time> em segundos."""
        partes = [int(p) for p in texto.split(":")]
        while len(partes) < 3:
            partes.insert(0, 0)
        h, m, s = partes[-3:]
        return h * 3600 + m * 60 + s

    def to_dict(self):
        return {
            "id": self.id,
            "jogo_id": self.jogo_id,
            "data": self.data.isoformat(),
            "tempo_duracao": self.tempo_formatado,
            "resultado": self.resultado,
            "causa_morte": self.causa_morte,
        }
