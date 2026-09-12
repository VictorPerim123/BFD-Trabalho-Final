from app.extensions import db
from app.models import Jogo, Categoria, RunDiario, BuildAnotacao
from app.models.jogo import STATUS_VALIDOS
from app.models.run_diario import RESULTADOS_VALIDOS


class ErroDeValidacao(ValueError):
    """Erro de regra de negócio (dados inválidos), tratado pelas rotas como HTTP 400."""


class RecursoNaoEncontrado(LookupError):
    """Jogo/run/build inexistente OU pertencente a outro usuário (tratado como HTTP 404)."""


class BacklogService:
    def __init__(self, usuario):
        self.usuario = usuario

    # ------------------------------------------------------------------ #
    # Jogos
    # ------------------------------------------------------------------ #
    def listar_jogos(self):
        return self.usuario.jogos.order_by(Jogo.titulo.asc()).all()

    def obter_jogo(self, jogo_id):
        jogo = Jogo.query.filter_by(id=jogo_id, usuario_id=self.usuario.id).first()
        if jogo is None:
            raise RecursoNaoEncontrado(f"Jogo {jogo_id} não encontrado para este usuário.")
        return jogo

    def criar_jogo(self, dados):
        titulo, status, nota, categorias_nomes = self._validar_dados_jogo(dados)

        jogo = Jogo(
            usuario_id=self.usuario.id,
            titulo=titulo,
            status=status,
            nota=nota,
            tempo_jogado_horas=int(dados.get("tempo_jogado_horas") or 0),
            total_conquistas=int(dados.get("total_conquistas") or 0),
            conquistas_obtidas=int(dados.get("conquistas_obtidas") or 0),
            steam_appid=dados.get("steam_appid"),
        )
        self._sincronizar_categorias(jogo, categorias_nomes)

        db.session.add(jogo)
        db.session.commit()
        return jogo

    def atualizar_jogo(self, jogo_id, dados):
        jogo = self.obter_jogo(jogo_id)
        titulo, status, nota, categorias_nomes = self._validar_dados_jogo(dados)

        jogo.titulo = titulo
        jogo.status = status
        jogo.nota = nota
        if "tempo_jogado_horas" in dados:
            jogo.tempo_jogado_horas = int(dados.get("tempo_jogado_horas") or 0)
        if "total_conquistas" in dados:
            jogo.total_conquistas = int(dados.get("total_conquistas") or 0)
        if "conquistas_obtidas" in dados:
            jogo.conquistas_obtidas = int(dados.get("conquistas_obtidas") or 0)
        self._sincronizar_categorias(jogo, categorias_nomes)

        db.session.commit()
        return jogo

    def excluir_jogo(self, jogo_id):
        jogo = self.obter_jogo(jogo_id)
        db.session.delete(jogo)
        db.session.commit()

    def _validar_dados_jogo(self, dados):
        titulo = (dados.get("titulo") or "").strip()
        if not titulo:
            raise ErroDeValidacao("O título do jogo é obrigatório.")
        if len(titulo) > 160:
            raise ErroDeValidacao("O título do jogo deve ter no máximo 160 caracteres.")

        status = dados.get("status") or "quero_jogar"
        if status not in STATUS_VALIDOS:
            raise ErroDeValidacao(f"Status inválido: {status!r}. Use um de {STATUS_VALIDOS}.")

        nota = dados.get("nota")
        if nota is not None and nota != "":
            try:
                nota = float(nota)
            except (TypeError, ValueError):
                raise ErroDeValidacao("A nota deve ser um número.")
            if not (0 <= nota <= 10):
                raise ErroDeValidacao("A nota deve estar entre 0 e 10.")
        else:
            nota = None

        categorias_raw = dados.get("categorias") or []
        if isinstance(categorias_raw, str):
            categorias_raw = [c.strip() for c in categorias_raw.split(",")]
        categorias_nomes = [c for c in (c.strip() for c in categorias_raw) if c]

        return titulo, status, nota, categorias_nomes

    def _sincronizar_categorias(self, jogo, nomes_categorias):
        """Associa `jogo` às categorias informadas, criando (por usuário) as
        que ainda não existirem — evita duplicatas como 'RPG' e 'rpg'."""
        categorias = []
        for nome in nomes_categorias:
            categoria = Categoria.query.filter_by(usuario_id=self.usuario.id, nome=nome).first()
            if categoria is None:
                categoria = Categoria(usuario_id=self.usuario.id, nome=nome)
                db.session.add(categoria)
            categorias.append(categoria)
        jogo.categorias = categorias

    # ------------------------------------------------------------------ #
    # Runs
    # ------------------------------------------------------------------ #
    def listar_runs(self):
        return (
            RunDiario.query.join(Jogo)
            .filter(Jogo.usuario_id == self.usuario.id)
            .order_by(RunDiario.data.desc(), RunDiario.id.desc())
            .all()
        )

    def registrar_run(self, dados):
        jogo = self.obter_jogo(dados.get("jogo_id"))

        resultado = dados.get("resultado")
        if resultado not in RESULTADOS_VALIDOS:
            raise ErroDeValidacao(f"Resultado inválido: {resultado!r}. Use um de {RESULTADOS_VALIDOS}.")

        tempo_duracao = dados.get("tempo_duracao")
        if not tempo_duracao:
            raise ErroDeValidacao("Informe o tempo de duração da run.")
        try:
            duracao_segundos = RunDiario.segundos_a_partir_de_hhmmss(tempo_duracao)
        except (ValueError, AttributeError):
            raise ErroDeValidacao("Tempo de duração inválido — use o formato HH:MM:SS.")

        from datetime import date

        try:
            data_run = date.fromisoformat(dados["data"]) if dados.get("data") else date.today()
        except ValueError:
            raise ErroDeValidacao("Data inválida — use o formato AAAA-MM-DD.")

        run = RunDiario(
            jogo_id=jogo.id,
            data=data_run,
            duracao_segundos=duracao_segundos,
            resultado=resultado,
            causa_morte=(dados.get("causa_morte") or None) if resultado == "derrota" else None,
        )
        db.session.add(run)
        db.session.commit()
        return run

    def obter_run(self, run_id):
        run = (
            RunDiario.query.join(Jogo)
            .filter(RunDiario.id == run_id, Jogo.usuario_id == self.usuario.id)
            .first()
        )
        if run is None:
            raise RecursoNaoEncontrado(f"Run {run_id} não encontrada para este usuário.")
        return run

    def excluir_run(self, run_id):
        run = self.obter_run(run_id)
        db.session.delete(run)
        db.session.commit()

    # ------------------------------------------------------------------ #
    # Builds
    # ------------------------------------------------------------------ #
    def listar_builds(self):
        return (
            BuildAnotacao.query.join(Jogo)
            .filter(Jogo.usuario_id == self.usuario.id)
            .order_by(BuildAnotacao.id.desc())
            .all()
        )

    def registrar_build(self, dados):
        jogo = self.obter_jogo(dados.get("jogo_id"))
        nome_build = (dados.get("nome_build") or "").strip()
        if not nome_build:
            raise ErroDeValidacao("O nome da build é obrigatório.")

        build = BuildAnotacao(
            jogo_id=jogo.id,
            nome_build=nome_build,
            detalhes_equipamento=(dados.get("detalhes_equipamento") or "").strip(),
            habilidades=(dados.get("habilidades") or "").strip(),
        )
        db.session.add(build)
        db.session.commit()
        return build

    def obter_build(self, build_id):
        build = (
            BuildAnotacao.query.join(Jogo)
            .filter(BuildAnotacao.id == build_id, Jogo.usuario_id == self.usuario.id)
            .first()
        )
        if build is None:
            raise RecursoNaoEncontrado(f"Build {build_id} não encontrada para este usuário.")
        return build

    def excluir_build(self, build_id):
        build = self.obter_build(build_id)
        db.session.delete(build)
        db.session.commit()
