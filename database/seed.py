import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  

load_dotenv()

from app import create_app 
from app.extensions import db  
from app.models import Usuario, Jogo, Categoria, RunDiario, BuildAnotacao  

JOGOS_EXEMPLO = [
    {
        "titulo": "Elden Ring",
        "status": "jogando",
        "nota": 9.5,
        "tempo_jogado_horas": 62,
        "total_conquistas": 42,
        "conquistas_obtidas": 27,
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
    {"jogo": "The Binding of Isaac", "data": "2026-08-09", "duracao_segundos": 32 * 60 + 15, "resultado": "derrota", "causa_morte": "Delirium na Cave"},
    {"jogo": "The Binding of Isaac", "data": "2026-08-08", "duracao_segundos": 21 * 60 + 40, "resultado": "vitoria", "causa_morte": None},
    {"jogo": "Dead Cells", "data": "2026-08-05", "duracao_segundos": 14 * 60 + 2, "resultado": "derrota", "causa_morte": "Concierge (DLC)"},
]

BUILDS_EXEMPLO = [
    {"jogo": "Elden Ring", "nome_build": "Sanguinário Faminto", "detalhes_equipamento": "Espada Rivers of Blood + Escudo Brass", "habilidades": "Foco em Sangramento (Arcane) e Vigor alto"},
    {"jogo": "Baldur's Gate 3", "nome_build": "Mago Elemental", "detalhes_equipamento": "Cajado do Arqui-mago + Anel de Absorção", "habilidades": "Bola de Fogo, Raio, Metamagia Estendida"},
]


def seed():
    app = create_app()
    with app.app_context():
        if Usuario.query.filter_by(username="demo").first():
            print("Usuário 'demo' já existe — banco já semeado. Nada a fazer.")
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
                causa_morte=dados["causa_morte"],
            )
            db.session.add(run)

        for dados in BUILDS_EXEMPLO:
            build = BuildAnotacao(
                jogo_id=jogos_por_titulo[dados["jogo"]].id,
                nome_build=dados["nome_build"],
                detalhes_equipamento=dados["detalhes_equipamento"],
                habilidades=dados["habilidades"],
            )
            db.session.add(build)

        db.session.commit()
        print("Banco semeado com sucesso.")
        print("Login de demonstração -> usuário: demo | senha: SavePoint123")


if __name__ == "__main__":
    seed()
