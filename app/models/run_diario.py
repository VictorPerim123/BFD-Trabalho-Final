from datetime import date as date_cls

from app.extensions import db

RESULTADOS_VALIDOS = ("vitoria", "derrota")


class RunDiario(db.Model):
    __tablename__ = "run_diario"
    __table_args__ = (
        db.CheckConstraint(f"resultado IN {RESULTADOS_VALIDOS}", name="ck_run_resultado_valido"),
        db.CheckConstraint("duracao_segundos > 0", name="ck_run_duracao_positiva"),
    )

    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogo.id", ondelete="CASCADE"), nullable=False, index=True)

    data = db.Column(db.Date, nullable=False, default=date_cls.today)
    duracao_segundos = db.Column(db.Integer, nullable=False, default=1)
    resultado = db.Column(db.String(10), nullable=False)
    causa_morte = db.Column(db.String(200), nullable=True)

    @property
    def tempo_formatado(self):
        h, resto = divmod(self.duracao_segundos, 3600)
        m, s = divmod(resto, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def segundos_a_partir_de_hhmmss(texto):
        if not isinstance(texto, str):
            raise ValueError("tempo deve ser texto")

        partes_texto = texto.strip().split(":")
        if len(partes_texto) not in (2, 3) or any(not p.isdigit() for p in partes_texto):
            raise ValueError("formato de tempo inválido")

        partes = [int(p) for p in partes_texto]
        if len(partes) == 2:
            h = 0
            m, s = partes
        else:
            h, m, s = partes

        if h < 0 or not (0 <= m <= 59) or not (0 <= s <= 59):
            raise ValueError("tempo fora do intervalo válido")

        total = h * 3600 + m * 60 + s
        if total <= 0:
            raise ValueError("a duração deve ser maior que zero")
        return total

    def to_dict(self):
        return {
            "id": self.id,
            "jogo_id": self.jogo_id,
            "data": self.data.isoformat(),
            "tempo_duracao": self.tempo_formatado,
            "resultado": self.resultado,
            "causa_morte": self.causa_morte,
        }
