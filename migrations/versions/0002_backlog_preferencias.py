from alembic import op
import sqlalchemy as sa

revision = "0002_backlog_preferencias"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    colunas = {coluna["name"] for coluna in sa.inspect(op.get_bind()).get_columns("jogo")}
    if "capa_url" not in colunas:
        with op.batch_alter_table("jogo") as batch_op:
            batch_op.add_column(sa.Column("capa_url", sa.String(length=500), nullable=True))

    with op.batch_alter_table("jogo") as batch_op:
        batch_op.add_column(sa.Column("favorito", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("prioridade", sa.String(length=10), nullable=False, server_default="normal"))
        batch_op.add_column(sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()))
        batch_op.create_check_constraint(
            "ck_jogo_prioridade_valida",
            "prioridade IN ('baixa', 'normal', 'alta')",
        )
        batch_op.create_unique_constraint(
            "uq_jogo_usuario_steam_appid",
            ["usuario_id", "steam_appid"],
        )
        batch_op.create_index("ix_jogo_status", ["status"], unique=False)
        batch_op.create_index("ix_jogo_prioridade", ["prioridade"], unique=False)
        batch_op.create_index("ix_jogo_steam_appid", ["steam_appid"], unique=False)
        batch_op.create_index("ix_jogo_criado_em", ["criado_em"], unique=False)


def downgrade():
    with op.batch_alter_table("jogo") as batch_op:
        batch_op.drop_index("ix_jogo_criado_em")
        batch_op.drop_index("ix_jogo_steam_appid")
        batch_op.drop_index("ix_jogo_prioridade")
        batch_op.drop_index("ix_jogo_status")
        batch_op.drop_constraint("uq_jogo_usuario_steam_appid", type_="unique")
        batch_op.drop_constraint("ck_jogo_prioridade_valida", type_="check")
        batch_op.drop_column("atualizado_em")
        batch_op.drop_column("prioridade")
        batch_op.drop_column("favorito")
