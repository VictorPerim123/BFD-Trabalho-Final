from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def _tem_tabela(nome):
    return sa.inspect(op.get_bind()).has_table(nome)


def _tem_indice(tabela, nome):
    if not _tem_tabela(tabela):
        return False
    return any(indice["name"] == nome for indice in sa.inspect(op.get_bind()).get_indexes(tabela))


def upgrade():
    if not _tem_tabela("usuario"):
        op.create_table(
            "usuario",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=120), nullable=False),
            sa.Column("username", sa.String(length=60), nullable=False),
            sa.Column("email", sa.String(length=160), nullable=False),
            sa.Column("senha_hash", sa.String(length=255), nullable=False),
            sa.Column("steam_id", sa.String(length=32), nullable=True),
            sa.Column("criado_em", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
            sa.UniqueConstraint("username"),
        )
    if not _tem_indice("usuario", "ix_usuario_email"):
        op.create_index("ix_usuario_email", "usuario", ["email"], unique=True)
    if not _tem_indice("usuario", "ix_usuario_username"):
        op.create_index("ix_usuario_username", "usuario", ["username"], unique=True)

    if not _tem_tabela("categoria"):
        op.create_table(
            "categoria",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("usuario_id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=60), nullable=False),
            sa.Column("cor_hex", sa.String(length=7), nullable=False),
            sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("usuario_id", "nome", name="uq_categoria_usuario_nome"),
        )

    if not _tem_tabela("jogo"):
        op.create_table(
            "jogo",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("usuario_id", sa.Integer(), nullable=False),
            sa.Column("titulo", sa.String(length=160), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("nota", sa.Float(), nullable=True),
            sa.Column("tempo_jogado_horas", sa.Integer(), nullable=False),
            sa.Column("total_conquistas", sa.Integer(), nullable=False),
            sa.Column("conquistas_obtidas", sa.Integer(), nullable=False),
            sa.Column("steam_appid", sa.Integer(), nullable=True),
            sa.Column("capa_url", sa.String(length=500), nullable=True),
            sa.Column("criado_em", sa.DateTime(), nullable=True),
            sa.CheckConstraint("conquistas_obtidas <= total_conquistas", name="ck_jogo_conquistas_consistentes"),
            sa.CheckConstraint("conquistas_obtidas >= 0", name="ck_jogo_conquistas_obtidas_nao_negativo"),
            sa.CheckConstraint("nota IS NULL OR (nota >= 0 AND nota <= 10)", name="ck_jogo_nota_intervalo"),
            sa.CheckConstraint("status IN ('quero_jogar', 'jogando', 'zerado', 'platinado', 'abandonado')", name="ck_jogo_status_valido"),
            sa.CheckConstraint("tempo_jogado_horas >= 0", name="ck_jogo_tempo_nao_negativo"),
            sa.CheckConstraint("total_conquistas >= 0", name="ck_jogo_total_conquistas_nao_negativo"),
            sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _tem_indice("jogo", "ix_jogo_usuario_id"):
        op.create_index("ix_jogo_usuario_id", "jogo", ["usuario_id"], unique=False)

    if not _tem_tabela("jogo_categoria"):
        op.create_table(
            "jogo_categoria",
            sa.Column("jogo_id", sa.Integer(), nullable=False),
            sa.Column("categoria_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["categoria_id"], ["categoria.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["jogo_id"], ["jogo.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("jogo_id", "categoria_id"),
        )

    if not _tem_tabela("run_diario"):
        op.create_table(
            "run_diario",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("jogo_id", sa.Integer(), nullable=False),
            sa.Column("data", sa.Date(), nullable=False),
            sa.Column("duracao_segundos", sa.Integer(), nullable=False),
            sa.Column("resultado", sa.String(length=10), nullable=False),
            sa.Column("causa_morte", sa.String(length=200), nullable=True),
            sa.CheckConstraint("duracao_segundos > 0", name="ck_run_duracao_positiva"),
            sa.CheckConstraint("resultado IN ('vitoria', 'derrota')", name="ck_run_resultado_valido"),
            sa.ForeignKeyConstraint(["jogo_id"], ["jogo.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _tem_indice("run_diario", "ix_run_diario_jogo_id"):
        op.create_index("ix_run_diario_jogo_id", "run_diario", ["jogo_id"], unique=False)

    if not _tem_tabela("build_anotacao"):
        op.create_table(
            "build_anotacao",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("jogo_id", sa.Integer(), nullable=False),
            sa.Column("nome_build", sa.String(length=120), nullable=False),
            sa.Column("detalhes_equipamento", sa.Text(), nullable=True),
            sa.Column("habilidades", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["jogo_id"], ["jogo.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _tem_indice("build_anotacao", "ix_build_anotacao_jogo_id"):
        op.create_index("ix_build_anotacao_jogo_id", "build_anotacao", ["jogo_id"], unique=False)


def downgrade():
    op.drop_index("ix_build_anotacao_jogo_id", table_name="build_anotacao")
    op.drop_table("build_anotacao")
    op.drop_index("ix_run_diario_jogo_id", table_name="run_diario")
    op.drop_table("run_diario")
    op.drop_table("jogo_categoria")
    op.drop_index("ix_jogo_usuario_id", table_name="jogo")
    op.drop_table("jogo")
    op.drop_table("categoria")
    op.drop_index("ix_usuario_username", table_name="usuario")
    op.drop_index("ix_usuario_email", table_name="usuario")
    op.drop_table("usuario")
