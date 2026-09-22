from sqlalchemy import inspect, text

from app.extensions import db


def aplicar_migracoes_compatibilidade():

    inspector = inspect(db.engine)
    if "jogo" not in inspector.get_table_names():
        return

    colunas = {coluna["name"] for coluna in inspector.get_columns("jogo")}
    if "capa_url" not in colunas:
        with db.engine.begin() as conexao:
            conexao.execute(text("ALTER TABLE jogo ADD COLUMN capa_url VARCHAR(500)"))
