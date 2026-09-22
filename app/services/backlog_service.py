from datetime import date
import unicodedata

from app.extensions import db
from app.models import Jogo, Categoria, RunDiario, BuildAnotacao
from app.models.jogo import STATUS_VALIDOS
from app.models.run_diario import RESULTADOS_VALIDOS


class ErroDeValidacao(ValueError):
    """"""


class RecursoNaoEncontrado(LookupError):
    """"""


class BacklogService:
    def __init__(self, usuario):
        self.usuario = usuario

    @staticmethod
    def _validar_objeto(dados):
        if not isinstance(dados, dict):
            raise ErroDeValidacao("Os dados enviados devem ser um objeto JSON.")

    @staticmethod
    def _inteiro_nao_negativo(dados, campo, rotulo, padrao=0):
        valor = dados.get(campo, padrao)
        if valor is None or valor == "":
            return padrao
        if isinstance(valor, bool):
            raise ErroDeValidacao(f"{rotulo} deve ser um número inteiro.")

        if isinstance(valor, str):
            texto = valor.strip()
            if not texto or not texto.lstrip("+-").isdigit():
                raise ErroDeValidacao(f"{rotulo} deve ser um número inteiro.")
            numero = int(texto)
        elif isinstance(valor, float):
            if not valor.is_integer():
                raise ErroDeValidacao(f"{rotulo} deve ser um número inteiro.")
            numero = int(valor)
        else:
            try:
                numero = int(valor)
            except (TypeError, ValueError):
                raise ErroDeValidacao(f"{rotulo} deve ser um número inteiro.")

        if numero < 0:
            raise ErroDeValidacao(f"{rotulo} não pode ser negativo.")
        return numero

    @staticmethod
    def _inteiro_positivo(valor, rotulo):
        if isinstance(valor, bool):
            raise ErroDeValidacao(f"{rotulo} inválido.")
        if isinstance(valor, str):
            texto = valor.strip()
            if not texto or not texto.lstrip("+").isdigit():
                raise ErroDeValidacao(f"{rotulo} inválido.")
            numero = int(texto)
        elif isinstance(valor, float):
            if not valor.is_integer():
                raise ErroDeValidacao(f"{rotulo} inválido.")
            numero = int(valor)
        else:
            try:
                numero = int(valor)
            except (TypeError, ValueError):
                raise ErroDeValidacao(f"{rotulo} inválido.")
        if numero <= 0:
            raise ErroDeValidacao(f"{rotulo} inválido.")
        return numero

    @staticmethod
    def _normalizar_texto(valor):
        return " ".join(unicodedata.normalize("NFKC", valor).casefold().split())

    @staticmethod
    def _texto(valor, rotulo, *, obrigatorio=False, maximo=None):
        if valor is None:
            texto = ""
        elif not isinstance(valor, str):
            raise ErroDeValidacao(f"{rotulo} deve ser um texto.")
        else:
            texto = valor.strip()
        if obrigatorio and not texto:
            raise ErroDeValidacao(f"{rotulo} é obrigatório.")
        if maximo is not None and len(texto) > maximo:
            raise ErroDeValidacao(f"{rotulo} deve ter no máximo {maximo} caracteres.")
        return texto

    def listar_jogos(self):
        return self.usuario.jogos.order_by(Jogo.titulo.asc()).all()

    def obter_jogo(self, jogo_id):
        jogo = Jogo.query.filter_by(id=jogo_id, usuario_id=self.usuario.id).first()
        if jogo is None:
            raise RecursoNaoEncontrado(f"Jogo {jogo_id} não encontrado para este usuário.")
        return jogo

    def criar_jogo(self, dados, *, commit=True):
        valores = self._validar_dados_jogo(dados)
        jogo = self._montar_jogo(valores)
        db.session.add(jogo)
        if commit:
            db.session.commit()
        return jogo

    def _montar_jogo(self, valores):
        jogo = Jogo(
            usuario_id=self.usuario.id,
            titulo=valores["titulo"],
            status=valores["status"],
            nota=valores["nota"],
            tempo_jogado_horas=valores["tempo_jogado_horas"],
            total_conquistas=valores["total_conquistas"],
            conquistas_obtidas=valores["conquistas_obtidas"],
            steam_appid=valores["steam_appid"],
        )
        self._sincronizar_categorias(jogo, valores["categorias"])
        return jogo

    def atualizar_jogo(self, jogo_id, dados):
        jogo = self.obter_jogo(jogo_id)
        valores = self._validar_dados_jogo(dados)

        jogo.titulo = valores["titulo"]
        jogo.status = valores["status"]
        jogo.nota = valores["nota"]
        jogo.tempo_jogado_horas = valores["tempo_jogado_horas"]
        jogo.total_conquistas = valores["total_conquistas"]
        jogo.conquistas_obtidas = valores["conquistas_obtidas"]
        self._sincronizar_categorias(jogo, valores["categorias"])

        db.session.commit()
        return jogo

    def excluir_jogo(self, jogo_id):
        jogo = self.obter_jogo(jogo_id)
        db.session.delete(jogo)
        db.session.commit()

    def _validar_dados_jogo(self, dados):
        self._validar_objeto(dados)

        titulo = self._texto(
            dados.get("titulo"), "O título do jogo", obrigatorio=True, maximo=160
        )

        status = dados.get("status") or "quero_jogar"
        if status not in STATUS_VALIDOS:
            raise ErroDeValidacao(f"Status inválido: {status!r}. Use um de {STATUS_VALIDOS}.")

        nota = dados.get("nota")
        if nota is not None and nota != "":
            if isinstance(nota, bool):
                raise ErroDeValidacao("A nota deve ser um número.")
            try:
                nota = float(nota)
            except (TypeError, ValueError):
                raise ErroDeValidacao("A nota deve ser um número.")
            if not (0 <= nota <= 10):
                raise ErroDeValidacao("A nota deve estar entre 0 e 10.")
        else:
            nota = None

        tempo = self._inteiro_nao_negativo(dados, "tempo_jogado_horas", "O tempo jogado")
        total = self._inteiro_nao_negativo(dados, "total_conquistas", "O total de conquistas")
        obtidas = self._inteiro_nao_negativo(dados, "conquistas_obtidas", "As conquistas obtidas")
        if obtidas > total:
            raise ErroDeValidacao("Conquistas obtidas não podem ultrapassar o total de conquistas.")

        categorias_raw = dados.get("categorias") or []
        if isinstance(categorias_raw, str):
            categorias_raw = categorias_raw.split(",")
        if not isinstance(categorias_raw, (list, tuple)):
            raise ErroDeValidacao("Categorias devem ser uma lista ou nomes separados por vírgula.")

        categorias = []
        vistos = set()
        for valor in categorias_raw:
            if not isinstance(valor, str):
                raise ErroDeValidacao("Cada categoria deve ser um texto.")
            nome = valor.strip()
            if not nome:
                continue
            if len(nome) > 60:
                raise ErroDeValidacao("Cada categoria deve ter no máximo 60 caracteres.")
            chave = self._normalizar_texto(nome)
            if chave not in vistos:
                vistos.add(chave)
                categorias.append(nome)

        steam_appid = dados.get("steam_appid")
        if steam_appid in (None, ""):
            steam_appid = None
        else:
            steam_appid = self._inteiro_positivo(steam_appid, "Steam AppID")

        return {
            "titulo": titulo,
            "status": status,
            "nota": nota,
            "tempo_jogado_horas": tempo,
            "total_conquistas": total,
            "conquistas_obtidas": obtidas,
            "categorias": categorias,
            "steam_appid": steam_appid,
        }

    def _sincronizar_categorias(self, jogo, nomes_categorias):
        existentes = {
            self._normalizar_texto(categoria.nome): categoria
            for categoria in Categoria.query.filter_by(usuario_id=self.usuario.id).all()
        }
        categorias = []
        for nome in nomes_categorias:
            chave = self._normalizar_texto(nome)
            categoria = existentes.get(chave)
            if categoria is None:
                categoria = Categoria(usuario_id=self.usuario.id, nome=nome)
                db.session.add(categoria)
                existentes[chave] = categoria
            categorias.append(categoria)
        jogo.categorias = categorias

    def importar_jogos_steam(self, biblioteca):
        if not isinstance(biblioteca, list):
            raise ErroDeValidacao("A biblioteca Steam recebida é inválida.")

        jogos_existentes = Jogo.query.filter_by(usuario_id=self.usuario.id).all()
        por_appid = {jogo.steam_appid: jogo for jogo in jogos_existentes if jogo.steam_appid is not None}
        por_titulo = {self._normalizar_texto(jogo.titulo): jogo for jogo in jogos_existentes}

        importados = 0
        vinculados = 0
        ignorados = 0

        try:
            for item in biblioteca:
                if not isinstance(item, dict):
                    raise ErroDeValidacao("A Steam retornou um item de jogo inválido.")

                appid = self._inteiro_positivo(item.get("steam_appid"), "Steam AppID")
                titulo = self._texto(
                    item.get("titulo"), "O título do jogo", obrigatorio=True, maximo=160
                )
                tempo = self._inteiro_nao_negativo(
                    item, "tempo_jogado_horas", "O tempo jogado"
                )

                if appid in por_appid:
                    ignorados += 1
                    continue

                chave_titulo = self._normalizar_texto(titulo)
                jogo_manual = por_titulo.get(chave_titulo)
                if jogo_manual is not None and jogo_manual.steam_appid is None:
                    jogo_manual.steam_appid = appid
                    jogo_manual.tempo_jogado_horas = max(jogo_manual.tempo_jogado_horas, tempo)
                    por_appid[appid] = jogo_manual
                    vinculados += 1
                    continue

                jogo = self.criar_jogo(
                    {
                        "titulo": titulo,
                        "status": "quero_jogar",
                        "tempo_jogado_horas": tempo,
                        "steam_appid": appid,
                    },
                    commit=False,
                )
                por_appid[appid] = jogo
                por_titulo.setdefault(chave_titulo, jogo)
                importados += 1

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {"importados": importados, "vinculados": vinculados, "ignorados": ignorados}

    def listar_runs(self):
        return (
            RunDiario.query.join(Jogo)
            .filter(Jogo.usuario_id == self.usuario.id)
            .order_by(RunDiario.data.desc(), RunDiario.id.desc())
            .all()
        )

    def obter_run(self, run_id):
        run = (
            RunDiario.query.join(Jogo)
            .filter(RunDiario.id == run_id, Jogo.usuario_id == self.usuario.id)
            .first()
        )
        if run is None:
            raise RecursoNaoEncontrado(f"Run {run_id} não encontrada para este usuário.")
        return run

    def _validar_dados_run(self, dados):
        self._validar_objeto(dados)
        jogo_id = self._inteiro_positivo(dados.get("jogo_id"), "Jogo")
        jogo = self.obter_jogo(jogo_id)

        resultado = dados.get("resultado")
        if resultado not in RESULTADOS_VALIDOS:
            raise ErroDeValidacao(f"Resultado inválido: {resultado!r}. Use um de {RESULTADOS_VALIDOS}.")

        tempo_duracao = dados.get("tempo_duracao")
        if not tempo_duracao:
            raise ErroDeValidacao("Informe o tempo de duração da run.")
        try:
            duracao_segundos = RunDiario.segundos_a_partir_de_hhmmss(tempo_duracao)
        except (TypeError, ValueError, AttributeError):
            raise ErroDeValidacao(
                "Tempo de duração inválido — use HH:MM:SS ou MM:SS e informe uma duração maior que zero."
            )

        data_texto = dados.get("data")
        if not isinstance(data_texto, str) or not data_texto.strip():
            raise ErroDeValidacao("Informe a data da run.")
        try:
            data_run = date.fromisoformat(data_texto.strip())
        except (TypeError, ValueError):
            raise ErroDeValidacao("Data inválida — use o formato AAAA-MM-DD.")

        causa = (
            self._texto(dados.get("causa_morte"), "A observação da run", maximo=200)
            if resultado == "derrota"
            else ""
        )

        return jogo, resultado, duracao_segundos, data_run, causa or None

    def registrar_run(self, dados):
        jogo, resultado, duracao, data_run, causa = self._validar_dados_run(dados)
        run = RunDiario(
            jogo_id=jogo.id,
            data=data_run,
            duracao_segundos=duracao,
            resultado=resultado,
            causa_morte=causa,
        )
        db.session.add(run)
        db.session.commit()
        return run

    def atualizar_run(self, run_id, dados):
        run = self.obter_run(run_id)
        jogo, resultado, duracao, data_run, causa = self._validar_dados_run(dados)
        run.jogo_id = jogo.id
        run.data = data_run
        run.duracao_segundos = duracao
        run.resultado = resultado
        run.causa_morte = causa
        db.session.commit()
        return run

    def excluir_run(self, run_id):
        run = self.obter_run(run_id)
        db.session.delete(run)
        db.session.commit()

    def listar_builds(self):
        return (
            BuildAnotacao.query.join(Jogo)
            .filter(Jogo.usuario_id == self.usuario.id)
            .order_by(BuildAnotacao.id.desc())
            .all()
        )

    def obter_build(self, build_id):
        build = (
            BuildAnotacao.query.join(Jogo)
            .filter(BuildAnotacao.id == build_id, Jogo.usuario_id == self.usuario.id)
            .first()
        )
        if build is None:
            raise RecursoNaoEncontrado(f"Build {build_id} não encontrada para este usuário.")
        return build

    def _validar_dados_build(self, dados):
        self._validar_objeto(dados)
        jogo_id = self._inteiro_positivo(dados.get("jogo_id"), "Jogo")
        jogo = self.obter_jogo(jogo_id)
        nome_build = self._texto(
            dados.get("nome_build"), "O nome da build", obrigatorio=True, maximo=120
        )
        equipamento = self._texto(dados.get("detalhes_equipamento"), "O equipamento") or None
        habilidades = self._texto(dados.get("habilidades"), "As habilidades") or None
        return jogo, nome_build, equipamento, habilidades

    def registrar_build(self, dados):
        jogo, nome, equipamento, habilidades = self._validar_dados_build(dados)
        build = BuildAnotacao(
            jogo_id=jogo.id,
            nome_build=nome,
            detalhes_equipamento=equipamento,
            habilidades=habilidades,
        )
        db.session.add(build)
        db.session.commit()
        return build

    def atualizar_build(self, build_id, dados):
        build = self.obter_build(build_id)
        jogo, nome, equipamento, habilidades = self._validar_dados_build(dados)
        build.jogo_id = jogo.id
        build.nome_build = nome
        build.detalhes_equipamento = equipamento
        build.habilidades = habilidades
        db.session.commit()
        return build

    def excluir_build(self, build_id):
        build = self.obter_build(build_id)
        db.session.delete(build)
        db.session.commit()

    def calcular_estatisticas_dashboard(self):
        jogos = self.listar_jogos()
        runs = self.listar_runs()

        zerados = sum(1 for j in jogos if j.status in ("zerado", "platinado"))
        horas_totais = sum(j.tempo_jogado_horas for j in jogos)
        notas = [j.nota for j in jogos if j.nota is not None]
        nota_media = round(sum(notas) / len(notas), 1) if notas else None

        return {
            "jogos_zerados": zerados,
            "horas_totais": horas_totais,
            "nota_media": nota_media,
            "total_runs": len(runs),
        }
