from alembic import op
import sqlalchemy as sa

revision = "0004_status_jogado"
down_revision = "0003_jornada_jogador"
branch_labels = None
depends_on = None


def _tem_constraint_status():
    checks = sa.inspect(op.get_bind()).get_check_constraints("jogo")
    return any(check.get("name") == "ck_jogo_status_valido" for check in checks)


def upgrade():
    with op.batch_alter_table("jogo") as batch_op:
        if _tem_constraint_status():
            batch_op.drop_constraint("ck_jogo_status_valido", type_="check")
        batch_op.create_check_constraint(
            "ck_jogo_status_valido",
            "status IN ('quero_jogar', 'jogando', 'jogado', 'zerado', 'platinado', 'abandonado')",
        )


def downgrade():
    op.execute("UPDATE jogo SET status = 'quero_jogar' WHERE status = 'jogado'")
    with op.batch_alter_table("jogo") as batch_op:
        if _tem_constraint_status():
            batch_op.drop_constraint("ck_jogo_status_valido", type_="check")
        batch_op.create_check_constraint(
            "ck_jogo_status_valido",
            "status IN ('quero_jogar', 'jogando', 'zerado', 'platinado', 'abandonado')",
        )
