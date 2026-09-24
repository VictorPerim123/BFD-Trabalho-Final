from alembic import op
import sqlalchemy as sa

revision = "0003_jornada_jogador"
down_revision = "0002_backlog_preferencias"
branch_labels = None
depends_on = None


def _tem_tabela(nome):
    return sa.inspect(op.get_bind()).has_table(nome)


def upgrade():
    if not _tem_tabela("conquista_steam"):
        op.create_table(
            "conquista_steam",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("jogo_id", sa.Integer(), nullable=False),
            sa.Column("api_name", sa.String(length=160), nullable=False),
            sa.Column("nome", sa.String(length=200), nullable=True),
            sa.Column("descricao", sa.Text(), nullable=True),
            sa.Column("icone_url", sa.String(length=500), nullable=True),
            sa.Column("icone_bloqueada_url", sa.String(length=500), nullable=True),
            sa.Column("desbloqueada", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("desbloqueada_em", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["jogo_id"], ["jogo.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("jogo_id", "api_name", name="uq_conquista_jogo_api_name"),
        )
        op.create_index("ix_conquista_steam_jogo_id", "conquista_steam", ["jogo_id"], unique=False)

    if not _tem_tabela("historico_jogo"):
        op.create_table(
            "historico_jogo",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("jogo_id", sa.Integer(), nullable=False),
            sa.Column("tipo", sa.String(length=40), nullable=False),
            sa.Column("descricao", sa.String(length=255), nullable=False),
            sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["jogo_id"], ["jogo.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_historico_jogo_jogo_criado",
            "historico_jogo",
            ["jogo_id", "criado_em"],
            unique=False,
        )

    if not _tem_tabela("desafio"):
        op.create_table(
            "desafio",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("usuario_id", sa.Integer(), nullable=False),
            sa.Column("jogo_id", sa.Integer(), nullable=True),
            sa.Column("titulo", sa.String(length=160), nullable=False),
            sa.Column("descricao", sa.Text(), nullable=True),
            sa.Column("tipo", sa.String(length=30), nullable=False, server_default="personalizado"),
            sa.Column("meta", sa.String(length=120), nullable=True),
            sa.Column("progresso", sa.String(length=120), nullable=True),
            sa.Column("data_inicio", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
            sa.Column("data_limite", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="ativo"),
            sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint(
                "status IN ('ativo', 'concluido', 'cancelado')",
                name="ck_desafio_status_valido",
            ),
            sa.CheckConstraint(
                "tipo IN ('backlog', 'conquistas', 'speedrun', 'personalizado')",
                name="ck_desafio_tipo_valido",
            ),
            sa.ForeignKeyConstraint(["jogo_id"], ["jogo.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_desafio_usuario_status",
            "desafio",
            ["usuario_id", "status"],
            unique=False,
        )

    if not _tem_tabela("build_atributo"):
        op.create_table(
            "build_atributo",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("build_id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=80), nullable=False),
            sa.Column("valor", sa.String(length=120), nullable=False),
            sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["build_id"], ["build_anotacao.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("build_id", "nome", name="uq_build_atributo_nome"),
        )
        op.create_index("ix_build_atributo_build_id", "build_atributo", ["build_id"], unique=False)

    colunas_build = {coluna["name"] for coluna in sa.inspect(op.get_bind()).get_columns("build_anotacao")}
    with op.batch_alter_table("build_anotacao") as batch_op:
        if "descricao" not in colunas_build:
            batch_op.add_column(sa.Column("descricao", sa.Text(), nullable=True))
        if "objetivo" not in colunas_build:
            batch_op.add_column(sa.Column("objetivo", sa.String(length=160), nullable=True))
        if "status" not in colunas_build:
            batch_op.add_column(sa.Column("status", sa.String(length=20), nullable=False, server_default="planejada"))
            batch_op.create_check_constraint(
                "ck_build_status_valido",
                "status IN ('planejada', 'em_uso', 'finalizada', 'experimental')",
            )
        if "nivel" not in colunas_build:
            batch_op.add_column(sa.Column("nivel", sa.Integer(), nullable=True))
        if "observacoes" not in colunas_build:
            batch_op.add_column(sa.Column("observacoes", sa.Text(), nullable=True))

    colunas_run = {coluna["name"] for coluna in sa.inspect(op.get_bind()).get_columns("run_diario")}
    with op.batch_alter_table("run_diario") as batch_op:
        if "build_id" not in colunas_run:
            batch_op.add_column(sa.Column("build_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_run_diario_build_id_build_anotacao",
                "build_anotacao",
                ["build_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_index("ix_run_diario_build_id", ["build_id"], unique=False)
        if "categoria" not in colunas_run:
            batch_op.add_column(sa.Column("categoria", sa.String(length=80), nullable=False, server_default="Casual"))
        if "observacao" not in colunas_run:
            batch_op.add_column(sa.Column("observacao", sa.String(length=300), nullable=True))
        if "eh_pb" not in colunas_run:
            batch_op.add_column(sa.Column("eh_pb", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_index("ix_run_jogo_categoria", ["jogo_id", "categoria"], unique=False)

    conexao = op.get_bind()
    vitorias = conexao.execute(
        sa.text(
            "SELECT id, jogo_id, categoria FROM run_diario "
            "WHERE resultado = 'vitoria' "
            "ORDER BY jogo_id, categoria, duracao_segundos, data, id"
        )
    ).mappings()
    chaves = set()
    for run in vitorias:
        chave = (run["jogo_id"], run["categoria"])
        if chave in chaves:
            continue
        chaves.add(chave)
        conexao.execute(
            sa.text("UPDATE run_diario SET eh_pb = :valor WHERE id = :id"),
            {"valor": True, "id": run["id"]},
        )


def downgrade():
    with op.batch_alter_table("run_diario") as batch_op:
        batch_op.drop_index("ix_run_jogo_categoria")
        batch_op.drop_index("ix_run_diario_build_id")
        batch_op.drop_constraint("fk_run_diario_build_id_build_anotacao", type_="foreignkey")
        batch_op.drop_column("eh_pb")
        batch_op.drop_column("observacao")
        batch_op.drop_column("categoria")
        batch_op.drop_column("build_id")

    with op.batch_alter_table("build_anotacao") as batch_op:
        batch_op.drop_constraint("ck_build_status_valido", type_="check")
        batch_op.drop_column("observacoes")
        batch_op.drop_column("nivel")
        batch_op.drop_column("status")
        batch_op.drop_column("objetivo")
        batch_op.drop_column("descricao")

    op.drop_index("ix_build_atributo_build_id", table_name="build_atributo")
    op.drop_table("build_atributo")
    op.drop_index("ix_desafio_usuario_status", table_name="desafio")
    op.drop_table("desafio")
    op.drop_index("ix_historico_jogo_jogo_criado", table_name="historico_jogo")
    op.drop_table("historico_jogo")
    op.drop_index("ix_conquista_steam_jogo_id", table_name="conquista_steam")
    op.drop_table("conquista_steam")
