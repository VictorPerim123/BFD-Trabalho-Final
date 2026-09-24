import logging
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models import BuildAnotacao, BuildAtributo, Categoria, Desafio, HistoricoJogo, Jogo, RunDiario, Usuario

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("seed")

JOGOS_EXEMPLO = [
    {
        "titulo": "Elden Ring",
        "status": "jogando",
        "nota": 9.5,
        "tempo_jogado_horas": 62,
        "total_conquistas": 42,
        "conquistas_obtidas": 32,
        "categorias": ["RPG", "Souls-like"],
    },
    {
        "titulo": "Hades II",
        "status": "quero_jogar",
        "nota": None,
        "tempo_jogado_horas": 0,
        "total_conquistas": 49,
        "conquistas_obtidas": 0,
        "categorias": ["Roguelike"],
    },
    {
        "titulo": "Cyberpunk 2077",
        "status": "zerado",
        "nota": 9.0,
        "tempo_jogado_horas": 87,
        "total_conquistas": 44,
        "conquistas_obtidas": 44,
        "categorias": ["RPG", "Ação"],
    },
    {
        "titulo": "Baldur's Gate 3",
        "status": "platinado",
        "nota": 10,
        "tempo_jogado_horas": 140,
        "total_conquistas": 54,
        "conquistas_obtidas": 54,
        "categorias": ["RPG", "Estratégia"],
    },
    {
        "titulo": "Dead Cells",
        "status": "abandonado",
        "nota": 6.5,
        "tempo_jogado_horas": 18,
        "total_conquistas": 30,
        "conquistas_obtidas": 9,
        "categorias": ["Roguelike", "Ação"],
    },
    {
        "titulo": "The Binding of Isaac",
        "status": "jogando",
        "nota": 8.5,
        "tempo_jogado_horas": 95,
        "total_conquistas": 60,
        "conquistas_obtidas": 33,
        "categorias": ["Roguelike"],
    },
]

RUNS_EXEMPLO = [
    {"jogo": "The Binding of Isaac", "data": "2026-08-09", "duracao_segundos": 32 * 60 + 15, "resultado": "derrota", "categoria": "Any%", "causa_morte": "Delirium na Cave", "eh_pb": False},
    {"jogo": "The Binding of Isaac", "data": "2026-08-08", "duracao_segundos": 21 * 60 + 40, "resultado": "vitoria", "categoria": "Any%", "causa_morte": None, "eh_pb": True},
    {"jogo": "Dead Cells", "data": "2026-08-05", "duracao_segundos": 14 * 60 + 2, "resultado": "derrota", "categoria": "Any%", "causa_morte": "Concierge (DLC)", "eh_pb": False},
]

BUILDS_EXEMPLO = [
    {
        "jogo": "Elden Ring",
        "nome_build": "Sanguinário Faminto",
        "descricao": "Build de sangramento para chefes e exploração em NG+.",
        "objetivo": "PvE / Bosses",
        "status": "em_uso",
        "nivel": 125,
        "detalhes_equipamento": "Rivers of Blood + White Mask",
        "habilidades": "Corpse Piler e buffs de sangramento",
        "atributos": [("Vigor", "50"), ("Destreza", "45"), ("Arcano", "55")],
    },
    {
        "jogo": "Baldur's Gate 3",
        "nome_build": "Mago Elemental",
        "descricao": "Controle e dano elemental à distância.",
        "objetivo": "Campanha",
        "status": "finalizada",
        "nivel": 12,
        "detalhes_equipamento": "Cajado do Arqui-mago + Anel de Absorção",
        "habilidades": "Bola de Fogo, Raio, Metamagia Estendida",
        "atributos": [("Inteligência", "20"), ("Constituição", "16")],
    },
]

DESAFIOS_EXEMPLO = [
    {
        "jogo": "Elden Ring",
        "titulo": "Chegar a 100% das conquistas",
        "tipo": "conquistas",
        "meta": "42 conquistas",
        "progresso": "32 / 42",
    },
    {
        "jogo": None,
        "titulo": "Finalizar 3 jogos do backlog",
        "tipo": "backlog",
        "meta": "3 jogos",
        "progresso": "1 / 3",
    },
]


def seed():
    app = create_app()
    with app.app_context():
        if Usuario.query.filter_by(username="demo").first():
            log.info("Usuário 'demo' já existe — banco já semeado. Nada a fazer.")
            return

        usuario = Usuario(nome="Jogador Demo", username="demo", email="demo@savepoint.dev")
        usuario.set_senha("SavePoint123")
        db.session.add(usuario)
        db.session.flush()

        categorias_cache = {}
        jogos_por_titulo = {}

        for dados_originais in JOGOS_EXEMPLO:
            dados = dict(dados_originais)
            categorias_nomes = dados.pop("categorias")
            jogo = Jogo(usuario_id=usuario.id, **dados)

            categorias_do_jogo = []
            for nome in categorias_nomes:
                chave = nome.lower()
                if chave not in categorias_cache:
                    categoria = Categoria(usuario_id=usuario.id, nome=nome)
                    db.session.add(categoria)
                    categorias_cache[chave] = categoria
                categorias_do_jogo.append(categorias_cache[chave])
            jogo.categorias = categorias_do_jogo

            db.session.add(jogo)
            jogos_por_titulo[dados["titulo"]] = jogo

        db.session.flush()

        for dados in RUNS_EXEMPLO:
            run = RunDiario(
                jogo_id=jogos_por_titulo[dados["jogo"]].id,
                data=date.fromisoformat(dados["data"]),
                duracao_segundos=dados["duracao_segundos"],
                resultado=dados["resultado"],
                categoria=dados["categoria"],
                causa_morte=dados["causa_morte"],
                eh_pb=dados["eh_pb"],
            )
            db.session.add(run)

        for dados in BUILDS_EXEMPLO:
            build = BuildAnotacao(
                jogo_id=jogos_por_titulo[dados["jogo"]].id,
                nome_build=dados["nome_build"],
                descricao=dados["descricao"],
                objetivo=dados["objetivo"],
                status=dados["status"],
                nivel=dados["nivel"],
                detalhes_equipamento=dados["detalhes_equipamento"],
                habilidades=dados["habilidades"],
            )
            build.atributos = [
                BuildAtributo(nome=nome, valor=valor, ordem=ordem)
                for ordem, (nome, valor) in enumerate(dados["atributos"])
            ]
            db.session.add(build)

        for dados in DESAFIOS_EXEMPLO:
            jogo = jogos_por_titulo.get(dados["jogo"]) if dados["jogo"] else None
            db.session.add(
                Desafio(
                    usuario_id=usuario.id,
                    jogo_id=jogo.id if jogo else None,
                    titulo=dados["titulo"],
                    tipo=dados["tipo"],
                    meta=dados["meta"],
                    progresso=dados["progresso"],
                )
            )

        db.session.add(
            HistoricoJogo(
                jogo_id=jogos_por_titulo["Elden Ring"].id,
                tipo="INICIADO",
                descricao="Jogo marcado como em andamento",
            )
        )
        db.session.add(
            HistoricoJogo(
                jogo_id=jogos_por_titulo["The Binding of Isaac"].id,
                tipo="PB_SPEEDRUN",
                descricao="Novo PB em Any%: 00:21:40",
            )
        )
        db.session.add(
            HistoricoJogo(
                jogo_id=jogos_por_titulo["Cyberpunk 2077"].id,
                tipo="ZERADO",
                descricao="Jogo marcado como zerado",
            )
        )
        db.session.add(
            HistoricoJogo(
                jogo_id=jogos_por_titulo["Baldur's Gate 3"].id,
                tipo="PLATINADO",
                descricao="Jogo marcado como platinado",
            )
        )

        db.session.commit()
        log.info("Banco semeado com sucesso.")
        log.info("Login de demonstração -> usuário: demo | senha: SavePoint123")


if __name__ == "__main__":
    seed()
