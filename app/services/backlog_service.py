from datetime import date, datetime, timedelta, timezone
import unicodedata

from sqlalchemy import Float, case, cast
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import (
    BuildAnotacao,
    BuildAtributo,
    Categoria,
    ConquistaSteam,
    Desafio,
    HistoricoJogo,
    Jogo,
    RunDiario,
)
from app.models.build_anotacao import STATUS_BUILD_VALIDOS
from app.models.desafio import STATUS_DESAFIO_VALIDOS, TIPOS_DESAFIO_VALIDOS
from app.models.jogo import PRIORIDADES_VALIDAS, STATUS_VALIDOS
from app.models.run_diario import RESULTADOS_VALIDOS


class ErroDeValidacao(ValueError):
    pass


class RecursoNaoEncontrado(LookupError):
    pass


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
    def _booleano(valor, rotulo):
        if isinstance(valor, bool):
            return valor
        if valor in (0, 1):
            return bool(valor)
        if isinstance(valor, str):
            normalizado = valor.strip().casefold()
            if normalizado in {"1", "true", "sim", "on"}:
                return True
            if normalizado in {"0", "false", "nao", "não", "off", ""}:
                return False
        raise ErroDeValidacao(f"{rotulo} deve ser verdadeiro ou falso.")

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

    @staticmethod
    def _data_iso(valor, rotulo, *, obrigatoria=False):
        if valor in (None, ""):
            if obrigatoria:
                raise ErroDeValidacao(f"{rotulo} é obrigatória.")
            return None
        if not isinstance(valor, str):
            raise ErroDeValidacao(f"{rotulo} inválida.")
        try:
            return date.fromisoformat(valor.strip())
        except ValueError:
            raise ErroDeValidacao(f"{rotulo} inválida — use AAAA-MM-DD.")

    def _registrar_historico(self, jogo, tipo, descricao):
        db.session.add(HistoricoJogo(jogo=jogo, tipo=tipo, descricao=descricao))

    def listar_jogos(self):
        return (
            self.usuario.jogos.options(selectinload(Jogo.categorias))
            .order_by(Jogo.titulo.asc())
            .all()
        )

    def listar_jogos_paginados(self, parametros):
        query = Jogo.query.options(selectinload(Jogo.categorias)).filter(
            Jogo.usuario_id == self.usuario.id
        )
        busca = (parametros.get("q") or "").strip()
        status = (parametros.get("status") or "").strip()
        categoria = (parametros.get("categoria") or "").strip()
        favorito = (parametros.get("favorito") or "").strip().casefold()
        prioridade = (parametros.get("prioridade") or "").strip()
        origem = (parametros.get("origem") or "").strip()
        com_conquistas = (parametros.get("com_conquistas") or "").strip().casefold()
        ordenar = (parametros.get("ordenar") or "titulo_asc").strip()

        if busca:
            query = query.filter(Jogo.titulo.ilike(f"%{busca}%"))
        if status:
            if status not in STATUS_VALIDOS:
                raise ErroDeValidacao("Filtro de status inválido.")
            query = query.filter(Jogo.status == status)
        if categoria:
            query = query.join(Jogo.categorias).filter(Categoria.nome == categoria).distinct()
        if favorito in {"1", "true", "sim"}:
            query = query.filter(Jogo.favorito.is_(True))
        elif favorito not in {"", "0", "false", "nao", "não"}:
            raise ErroDeValidacao("Filtro de favorito inválido.")
        if prioridade:
            if prioridade not in PRIORIDADES_VALIDAS:
                raise ErroDeValidacao("Filtro de prioridade inválido.")
            query = query.filter(Jogo.prioridade == prioridade)
        if origem == "steam":
            query = query.filter(Jogo.steam_appid.isnot(None))
        elif origem == "manual":
            query = query.filter(Jogo.steam_appid.is_(None))
        elif origem:
            raise ErroDeValidacao("Filtro de origem inválido.")
        if com_conquistas in {"1", "true", "sim"}:
            query = query.filter(Jogo.total_conquistas > 0)
        elif com_conquistas not in {"", "0", "false", "nao", "não"}:
            raise ErroDeValidacao("Filtro de conquistas inválido.")

        progresso = case(
            (Jogo.total_conquistas > 0, cast(Jogo.conquistas_obtidas, Float) / Jogo.total_conquistas),
            else_=0.0,
        )
        prioridade_ordem = case(
            (Jogo.prioridade == "alta", 3),
            (Jogo.prioridade == "normal", 2),
            else_=1,
        )
        ordenacoes = {
            "titulo_asc": (Jogo.titulo.asc(),),
            "titulo_desc": (Jogo.titulo.desc(),),
            "tempo_desc": (Jogo.tempo_jogado_horas.desc(), Jogo.titulo.asc()),
            "tempo_asc": (Jogo.tempo_jogado_horas.asc(), Jogo.titulo.asc()),
            "nota_desc": (Jogo.nota.desc(), Jogo.titulo.asc()),
            "recentes": (Jogo.criado_em.desc(), Jogo.id.desc()),
            "prioridade": (prioridade_ordem.desc(), Jogo.titulo.asc()),
            "progresso_desc": (progresso.desc(), Jogo.titulo.asc()),
        }
        if ordenar not in ordenacoes:
            raise ErroDeValidacao("Ordenação inválida.")
        query = query.order_by(*ordenacoes[ordenar])

        try:
            pagina = max(1, int(parametros.get("page", 1)))
            por_pagina = int(parametros.get("per_page", 24))
        except (TypeError, ValueError):
            raise ErroDeValidacao("Paginação inválida.")
        por_pagina = min(max(por_pagina, 1), 100)
        resultado = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        categorias = [
            item.nome
            for item in Categoria.query.filter_by(usuario_id=self.usuario.id)
            .order_by(Categoria.nome.asc())
            .all()
        ]
        return {
            "itens": [jogo.to_dict() for jogo in resultado.items],
            "paginacao": {
                "pagina": resultado.page,
                "por_pagina": resultado.per_page,
                "total": resultado.total,
                "paginas": resultado.pages,
                "tem_anterior": resultado.has_prev,
                "tem_proxima": resultado.has_next,
            },
            "filtros": {"categorias": categorias},
        }

    def obter_jogo(self, jogo_id):
        jogo = Jogo.query.filter_by(id=jogo_id, usuario_id=self.usuario.id).first()
        if jogo is None:
            raise RecursoNaoEncontrado(f"Jogo {jogo_id} não encontrado para este usuário.")
        return jogo

    def obter_jornada_jogo(self, jogo_id):
        jogo = self.obter_jogo(jogo_id)
        builds = (
            BuildAnotacao.query.options(selectinload(BuildAnotacao.atributos))
            .filter_by(jogo_id=jogo.id)
            .order_by(BuildAnotacao.id.desc())
            .all()
        )
        runs = (
            RunDiario.query.options(selectinload(RunDiario.build))
            .filter_by(jogo_id=jogo.id)
            .order_by(RunDiario.data.desc(), RunDiario.id.desc())
            .limit(10)
            .all()
        )
        desafios = (
            Desafio.query.filter_by(usuario_id=self.usuario.id, jogo_id=jogo.id)
            .order_by(Desafio.status.asc(), Desafio.id.desc())
            .all()
        )
        historico = (
            HistoricoJogo.query.filter_by(jogo_id=jogo.id)
            .order_by(HistoricoJogo.criado_em.desc(), HistoricoJogo.id.desc())
            .limit(20)
            .all()
        )
        conquistas = (
            ConquistaSteam.query.filter_by(jogo_id=jogo.id)
            .order_by(ConquistaSteam.desbloqueada.desc(), ConquistaSteam.nome.asc())
            .all()
        )
        pbs = (
            RunDiario.query.filter_by(jogo_id=jogo.id, eh_pb=True)
            .order_by(RunDiario.categoria.asc(), RunDiario.duracao_segundos.asc())
            .all()
        )
        build_ativa = next((build for build in builds if build.status == "em_uso"), None)
        desafios_ativos = [desafio for desafio in desafios if desafio.status == "ativo"]
        resumo = {
            "build_ativa": build_ativa,
            "pbs": pbs,
            "total_builds": len(builds),
            "total_runs": RunDiario.query.filter_by(jogo_id=jogo.id).count(),
            "desafios_ativos": len(desafios_ativos),
            "ultima_atividade": historico[0] if historico else None,
            "conquistas_faltantes": max(0, jogo.total_conquistas - jogo.conquistas_obtidas),
        }
        return {
            "jogo": jogo,
            "conquistas": conquistas,
            "builds": builds,
            "runs": runs,
            "desafios": desafios,
            "historico": historico,
            "resumo": resumo,
        }

    def criar_jogo(self, dados, *, commit=True):
        valores = self._validar_dados_jogo(dados)
        jogo = self._montar_jogo(valores)
        db.session.add(jogo)
        self._registrar_historico(jogo, "ADICIONADO", "Jogo adicionado ao backlog")
        if commit:
            db.session.commit()
        return jogo

    def _montar_jogo(self, valores):
        jogo = Jogo(
            usuario_id=self.usuario.id,
            titulo=valores["titulo"],
            status=valores["status"],
            nota=valores["nota"],
            favorito=valores["favorito"],
            prioridade=valores["prioridade"],
            tempo_jogado_horas=valores["tempo_jogado_horas"],
            total_conquistas=valores["total_conquistas"],
            conquistas_obtidas=valores["conquistas_obtidas"],
            steam_appid=valores["steam_appid"],
        )
        self._sincronizar_categorias(jogo, valores["categorias"])
        return jogo

    def atualizar_jogo(self, jogo_id, dados):
        jogo = self.obter_jogo(jogo_id)
        status_anterior = jogo.status
        valores = self._validar_dados_jogo(dados)
        jogo.titulo = valores["titulo"]
        jogo.status = valores["status"]
        jogo.nota = valores["nota"]
        jogo.favorito = valores["favorito"]
        jogo.prioridade = valores["prioridade"]
        jogo.tempo_jogado_horas = valores["tempo_jogado_horas"]
        jogo.total_conquistas = valores["total_conquistas"]
        jogo.conquistas_obtidas = valores["conquistas_obtidas"]
        self._sincronizar_categorias(jogo, valores["categorias"])
        if status_anterior != jogo.status:
            tipos = {
                "jogando": ("INICIADO", "Jogo marcado como em andamento"),
                "jogado": ("JOGADO", "Jogo marcado como já jogado"),
                "zerado": ("ZERADO", "Jogo marcado como zerado"),
                "platinado": ("PLATINADO", "Jogo marcado como platinado"),
                "abandonado": ("ABANDONADO", "Jogo marcado como abandonado"),
            }
            if jogo.status in tipos:
                tipo, descricao = tipos[jogo.status]
                self._registrar_historico(jogo, tipo, descricao)
        db.session.commit()
        return jogo

    def excluir_jogo(self, jogo_id):
        jogo = self.obter_jogo(jogo_id)
        db.session.delete(jogo)
        db.session.commit()

    def atualizar_preferencias_jogo(self, jogo_id, dados):
        self._validar_objeto(dados)
        jogo = self.obter_jogo(jogo_id)
        if "favorito" in dados:
            jogo.favorito = self._booleano(dados.get("favorito"), "Favorito")
        if "prioridade" in dados:
            prioridade = self._texto(dados.get("prioridade"), "A prioridade", obrigatorio=True)
            if prioridade not in PRIORIDADES_VALIDAS:
                raise ErroDeValidacao("Prioridade inválida.")
            jogo.prioridade = prioridade
        db.session.commit()
        return jogo

    def _validar_dados_jogo(self, dados):
        self._validar_objeto(dados)
        titulo = self._texto(dados.get("titulo"), "O título do jogo", obrigatorio=True, maximo=160)
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
            if not 0 <= nota <= 10:
                raise ErroDeValidacao("A nota deve estar entre 0 e 10.")
        else:
            nota = None

        favorito = self._booleano(dados.get("favorito", False), "Favorito")
        prioridade = dados.get("prioridade") or "normal"
        if prioridade not in PRIORIDADES_VALIDAS:
            raise ErroDeValidacao(f"Prioridade inválida: {prioridade!r}.")

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
            "favorito": favorito,
            "prioridade": prioridade,
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

    def prever_importacao_steam(
        self,
        biblioteca,
        *,
        classificar_status=False,
        reclassificar_existentes=False,
    ):
        if not isinstance(biblioteca, list):
            raise ErroDeValidacao("A biblioteca Steam recebida é inválida.")

        jogos_existentes = Jogo.query.filter_by(usuario_id=self.usuario.id).all()
        por_appid = {jogo.steam_appid: jogo for jogo in jogos_existentes if jogo.steam_appid is not None}
        por_titulo = {self._normalizar_texto(jogo.titulo): jogo for jogo in jogos_existentes}
        novos = vinculaveis = existentes = atualizacoes_previstas = sem_alteracao_prevista = 0
        status_reclassificados = status_preservados = 0
        falhas_conquistas = 0
        status_previstos = {status: 0 for status in STATUS_VALIDOS}

        for item in biblioteca:
            if not isinstance(item, dict):
                raise ErroDeValidacao("A Steam retornou um item de jogo inválido.")
            appid = self._inteiro_positivo(item.get("steam_appid"), "Steam AppID")
            titulo = self._texto(item.get("titulo"), "O título do jogo", obrigatorio=True, maximo=160)
            tempo = self._inteiro_nao_negativo(item, "tempo_jogado_horas", "O tempo jogado")

            if item.get("conquistas_sincronizadas") is False:
                falhas_conquistas += 1

            jogo = por_appid.get(appid)
            if jogo is not None:
                existentes += 1
                alteraria = tempo > jogo.tempo_jogado_horas
                if self._conquistas_foram_sincronizadas(item):
                    total = self._inteiro_nao_negativo(item, "total_conquistas", "O total de conquistas")
                    obtidas = self._inteiro_nao_negativo(item, "conquistas_obtidas", "As conquistas obtidas")
                    alteraria = alteraria or total != jogo.total_conquistas or obtidas != jogo.conquistas_obtidas
                if classificar_status and reclassificar_existentes and jogo.status == "quero_jogar":
                    novo_status = self._classificar_status_steam(item)
                    if novo_status != jogo.status:
                        alteraria = True
                        status_reclassificados += 1
                        status_previstos[novo_status] += 1
                    else:
                        status_preservados += 1
                else:
                    status_preservados += 1
                if alteraria:
                    atualizacoes_previstas += 1
                else:
                    sem_alteracao_prevista += 1
                continue

            jogo_manual = por_titulo.get(self._normalizar_texto(titulo))
            if jogo_manual is not None and jogo_manual.steam_appid is None:
                vinculaveis += 1
                atualizacoes_previstas += 1
                if classificar_status and reclassificar_existentes and jogo_manual.status == "quero_jogar":
                    novo_status = self._classificar_status_steam(item)
                    if novo_status != jogo_manual.status:
                        status_reclassificados += 1
                        status_previstos[novo_status] += 1
                    else:
                        status_preservados += 1
                else:
                    status_preservados += 1
                continue

            novos += 1
            novo_status = self._classificar_status_steam(item) if classificar_status else "quero_jogar"
            status_previstos[novo_status] += 1

        return {
            "novos": novos,
            "vinculaveis": vinculaveis,
            "existentes": existentes,
            "atualizacoes_previstas": atualizacoes_previstas,
            "sem_alteracao_prevista": sem_alteracao_prevista,
            "status_reclassificados": status_reclassificados,
            "status_preservados": status_preservados,
            "status_previstos": status_previstos,
            "falhas_conquistas": falhas_conquistas,
            "classificacao_automatica": classificar_status,
            "reclassificar_existentes": reclassificar_existentes,
        }

    def importar_jogos_steam(
        self,
        biblioteca,
        *,
        classificar_status=False,
        reclassificar_existentes=False,
    ):
        if not isinstance(biblioteca, list):
            raise ErroDeValidacao("A biblioteca Steam recebida é inválida.")
        jogos_existentes = Jogo.query.filter_by(usuario_id=self.usuario.id).all()
        por_appid = {jogo.steam_appid: jogo for jogo in jogos_existentes if jogo.steam_appid is not None}
        por_titulo = {self._normalizar_texto(jogo.titulo): jogo for jogo in jogos_existentes}
        importados = vinculados = atualizados = ignorados = 0
        status_classificados = 0
        conquistas_sincronizadas = conquistas_indisponiveis = conquistas_falharam = 0

        try:
            for item in biblioteca:
                if not isinstance(item, dict):
                    raise ErroDeValidacao("A Steam retornou um item de jogo inválido.")
                appid = self._inteiro_positivo(item.get("steam_appid"), "Steam AppID")
                titulo = self._texto(item.get("titulo"), "O título do jogo", obrigatorio=True, maximo=160)
                tempo = self._inteiro_nao_negativo(item, "tempo_jogado_horas", "O tempo jogado")

                if "conquistas_sincronizadas" in item:
                    if not item.get("conquistas_sincronizadas"):
                        conquistas_falharam += 1
                    elif item.get("conquistas_disponiveis", True):
                        conquistas_sincronizadas += 1
                    else:
                        conquistas_indisponiveis += 1

                jogo = por_appid.get(appid)
                if jogo is not None:
                    alterado = self._sincronizar_metadados_steam(jogo, item, tempo)
                    detalhes_alterados = self._sincronizar_conquistas_detalhadas(jogo, item)
                    status_alterado = False
                    if (
                        classificar_status
                        and reclassificar_existentes
                        and jogo.status == "quero_jogar"
                    ):
                        novo_status = self._classificar_status_steam(item)
                        if novo_status != jogo.status:
                            jogo.status = novo_status
                            status_alterado = True
                            status_classificados += 1
                    if alterado or detalhes_alterados or status_alterado:
                        atualizados += 1
                    else:
                        ignorados += 1
                    continue

                chave_titulo = self._normalizar_texto(titulo)
                jogo_manual = por_titulo.get(chave_titulo)
                if jogo_manual is not None and jogo_manual.steam_appid is None:
                    jogo_manual.steam_appid = appid
                    self._sincronizar_metadados_steam(jogo_manual, item, tempo)
                    self._sincronizar_conquistas_detalhadas(jogo_manual, item)
                    if (
                        classificar_status
                        and reclassificar_existentes
                        and jogo_manual.status == "quero_jogar"
                    ):
                        novo_status = self._classificar_status_steam(item)
                        if novo_status != jogo_manual.status:
                            jogo_manual.status = novo_status
                            status_classificados += 1
                    por_appid[appid] = jogo_manual
                    vinculados += 1
                    continue

                status_novo = (
                    self._classificar_status_steam(item)
                    if classificar_status
                    else "quero_jogar"
                )
                dados_novo = {
                    "titulo": titulo,
                    "status": status_novo,
                    "tempo_jogado_horas": tempo,
                    "steam_appid": appid,
                }
                if self._conquistas_foram_sincronizadas(item):
                    dados_novo["total_conquistas"] = self._inteiro_nao_negativo(item, "total_conquistas", "O total de conquistas")
                    dados_novo["conquistas_obtidas"] = self._inteiro_nao_negativo(item, "conquistas_obtidas", "As conquistas obtidas")
                jogo = self.criar_jogo(dados_novo, commit=False)
                jogo.capa_url = self._capa_steam(item)
                self._sincronizar_conquistas_detalhadas(jogo, item)
                por_appid[appid] = jogo
                por_titulo.setdefault(chave_titulo, jogo)
                importados += 1
                if classificar_status and status_novo != "quero_jogar":
                    status_classificados += 1
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        resultado = {
            "importados": importados,
            "vinculados": vinculados,
            "atualizados": atualizados,
            "ignorados": ignorados,
            "conquistas_sincronizadas": conquistas_sincronizadas,
            "conquistas_indisponiveis": conquistas_indisponiveis,
            "conquistas_falharam": conquistas_falharam,
        }
        if classificar_status:
            resultado["status_classificados"] = status_classificados
        return resultado

    def _classificar_status_steam(self, item):
        if self._conquistas_foram_sincronizadas(item):
            total = self._inteiro_nao_negativo(item, "total_conquistas", "O total de conquistas")
            obtidas = self._inteiro_nao_negativo(item, "conquistas_obtidas", "As conquistas obtidas")
            if total > 0 and obtidas == total:
                return "platinado"
        if item.get("atividade_recente"):
            return "jogando"
        minutos = self._inteiro_nao_negativo(
            item,
            "tempo_jogado_minutos",
            "O tempo jogado em minutos",
            padrao=0,
        )
        obtidas = self._inteiro_nao_negativo(
            item,
            "conquistas_obtidas",
            "As conquistas obtidas",
            padrao=0,
        )
        if minutos > 0 or item.get("tempo_jogado_horas", 0) or obtidas > 0:
            return "jogado"
        return "quero_jogar"

    @staticmethod
    def _conquistas_foram_sincronizadas(item):
        if "conquistas_sincronizadas" in item:
            return bool(item.get("conquistas_sincronizadas"))
        return "total_conquistas" in item and "conquistas_obtidas" in item

    def _capa_steam(self, item):
        capa = self._texto(item.get("capa_url"), "A URL da capa", maximo=500)
        if not capa:
            return None
        if not capa.startswith("https://"):
            raise ErroDeValidacao("A URL da capa retornada pela Steam é inválida.")
        return capa

    def _sincronizar_metadados_steam(self, jogo, item, tempo):
        alterado = False
        novo_tempo = max(jogo.tempo_jogado_horas, tempo)
        if novo_tempo != jogo.tempo_jogado_horas:
            jogo.tempo_jogado_horas = novo_tempo
            alterado = True
        capa = self._capa_steam(item)
        if capa and capa != jogo.capa_url:
            jogo.capa_url = capa
            alterado = True
        if self._conquistas_foram_sincronizadas(item):
            total = self._inteiro_nao_negativo(item, "total_conquistas", "O total de conquistas")
            obtidas = self._inteiro_nao_negativo(item, "conquistas_obtidas", "As conquistas obtidas")
            if obtidas > total:
                raise ErroDeValidacao("As conquistas obtidas retornadas pela Steam ultrapassam o total.")
            if total != jogo.total_conquistas or obtidas != jogo.conquistas_obtidas:
                anteriores = jogo.conquistas_obtidas
                jogo.total_conquistas = total
                jogo.conquistas_obtidas = obtidas
                alterado = True
                if obtidas != anteriores:
                    self._registrar_historico(jogo, "CONQUISTA", f"Progresso de conquistas atualizado: {obtidas}/{total}")
        return alterado

    def _sincronizar_conquistas_detalhadas(self, jogo, item):
        if not self._conquistas_foram_sincronizadas(item):
            return False
        detalhes = item.get("conquistas_detalhes")
        if detalhes is None:
            return False
        if not isinstance(detalhes, list):
            raise ErroDeValidacao("A lista detalhada de conquistas retornada pela Steam é inválida.")
        existentes = {conquista.api_name: conquista for conquista in jogo.conquistas_steam}
        recebidas = set()
        alterado = False
        for dados in detalhes:
            if not isinstance(dados, dict):
                continue
            api_name = self._texto(dados.get("api_name"), "O identificador da conquista", obrigatorio=True, maximo=160)
            recebidas.add(api_name)
            conquista = existentes.get(api_name)
            if conquista is None:
                conquista = ConquistaSteam(jogo=jogo, api_name=api_name)
                db.session.add(conquista)
                alterado = True
            nome = self._texto(dados.get("nome"), "O nome da conquista", maximo=200) or api_name
            if conquista.nome and conquista.nome != conquista.api_name and nome == api_name:
                nome = conquista.nome
            descricao = self._texto(dados.get("descricao"), "A descrição da conquista") or conquista.descricao
            icone = self._texto(dados.get("icone_url"), "O ícone da conquista", maximo=500) or None
            bloqueada = self._texto(dados.get("icone_bloqueada_url"), "O ícone bloqueado", maximo=500) or None
            desbloqueada = self._booleano(dados.get("desbloqueada", False), "Conquista desbloqueada")
            desbloqueada_em = ConquistaSteam.data_unlock(dados.get("unlocktime"))
            if desbloqueada and desbloqueada_em is None:
                desbloqueada_em = conquista.desbloqueada_em
            if not desbloqueada:
                desbloqueada_em = None
            valores = {
                "nome": nome,
                "descricao": descricao,
                "icone_url": icone or conquista.icone_url,
                "icone_bloqueada_url": bloqueada or conquista.icone_bloqueada_url,
                "desbloqueada": desbloqueada,
                "desbloqueada_em": desbloqueada_em,
            }
            for campo, valor in valores.items():
                if getattr(conquista, campo) != valor:
                    setattr(conquista, campo, valor)
                    alterado = True
        for api_name, conquista in existentes.items():
            if api_name not in recebidas:
                db.session.delete(conquista)
                alterado = True
        return alterado

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
        jogo = self.obter_jogo(self._inteiro_positivo(dados.get("jogo_id"), "Jogo"))
        resultado = dados.get("resultado")
        if resultado not in RESULTADOS_VALIDOS:
            raise ErroDeValidacao(f"Resultado inválido: {resultado!r}. Use um de {RESULTADOS_VALIDOS}.")
        tempo_duracao = dados.get("tempo_duracao")
        if not tempo_duracao:
            raise ErroDeValidacao("Informe o tempo de duração da run.")
        try:
            duracao_segundos = RunDiario.segundos_a_partir_de_hhmmss(tempo_duracao)
        except (TypeError, ValueError, AttributeError):
            raise ErroDeValidacao("Tempo de duração inválido — use HH:MM:SS ou MM:SS e informe uma duração maior que zero.")
        data_run = self._data_iso(dados.get("data"), "A data da run", obrigatoria=True)
        categoria = self._texto(dados.get("categoria") or "Casual", "A categoria", obrigatorio=True, maximo=80)
        causa = self._texto(dados.get("causa_morte"), "A causa da morte", maximo=200) if resultado == "derrota" else ""
        observacao = self._texto(dados.get("observacao"), "A observação da run", maximo=300) or None
        build = None
        build_id = dados.get("build_id")
        if build_id not in (None, "", 0, "0"):
            build = self.obter_build(self._inteiro_positivo(build_id, "Build"))
            if build.jogo_id != jogo.id:
                raise ErroDeValidacao("A build selecionada pertence a outro jogo.")
        return jogo, build, resultado, duracao_segundos, data_run, categoria, causa or None, observacao

    def _recalcular_pbs(self, jogo_id, categoria):
        runs = (
            RunDiario.query.filter_by(jogo_id=jogo_id, categoria=categoria, resultado="vitoria")
            .order_by(RunDiario.duracao_segundos.asc(), RunDiario.data.asc(), RunDiario.id.asc())
            .all()
        )
        for run in runs:
            run.eh_pb = False
        if runs:
            runs[0].eh_pb = True

    def registrar_run(self, dados):
        jogo, build, resultado, duracao, data_run, categoria, causa, observacao = self._validar_dados_run(dados)
        run = RunDiario(
            jogo_id=jogo.id,
            build_id=build.id if build else None,
            data=data_run,
            duracao_segundos=duracao,
            resultado=resultado,
            categoria=categoria,
            causa_morte=causa,
            observacao=observacao,
        )
        db.session.add(run)
        db.session.flush()
        self._recalcular_pbs(jogo.id, categoria)
        if run.eh_pb:
            self._registrar_historico(jogo, "PB_SPEEDRUN", f"Novo PB em {categoria}: {run.tempo_formatado}")
        db.session.commit()
        return run

    def atualizar_run(self, run_id, dados):
        run = self.obter_run(run_id)
        jogo_antigo_id = run.jogo_id
        categoria_antiga = run.categoria
        duracao_antiga = run.duracao_segundos
        era_pb = run.eh_pb
        jogo, build, resultado, duracao, data_run, categoria, causa, observacao = self._validar_dados_run(dados)
        run.jogo_id = jogo.id
        run.build_id = build.id if build else None
        run.data = data_run
        run.duracao_segundos = duracao
        run.resultado = resultado
        run.categoria = categoria
        run.causa_morte = causa
        run.observacao = observacao
        db.session.flush()
        self._recalcular_pbs(jogo_antigo_id, categoria_antiga)
        self._recalcular_pbs(jogo.id, categoria)
        if run.eh_pb and (
            not era_pb
            or duracao < duracao_antiga
            or jogo.id != jogo_antigo_id
            or categoria != categoria_antiga
        ):
            self._registrar_historico(jogo, "PB_SPEEDRUN", f"Novo PB em {categoria}: {run.tempo_formatado}")
        db.session.commit()
        return run

    def excluir_run(self, run_id):
        run = self.obter_run(run_id)
        jogo_id = run.jogo_id
        categoria = run.categoria
        db.session.delete(run)
        db.session.flush()
        self._recalcular_pbs(jogo_id, categoria)
        db.session.commit()

    def listar_builds(self):
        return (
            BuildAnotacao.query.options(selectinload(BuildAnotacao.atributos))
            .join(Jogo)
            .filter(Jogo.usuario_id == self.usuario.id)
            .order_by(BuildAnotacao.id.desc())
            .all()
        )

    def obter_build(self, build_id):
        build = (
            BuildAnotacao.query.options(selectinload(BuildAnotacao.atributos))
            .join(Jogo)
            .filter(BuildAnotacao.id == build_id, Jogo.usuario_id == self.usuario.id)
            .first()
        )
        if build is None:
            raise RecursoNaoEncontrado(f"Build {build_id} não encontrada para este usuário.")
        return build

    def _validar_atributos_build(self, atributos):
        if atributos in (None, ""):
            return []
        if not isinstance(atributos, list):
            raise ErroDeValidacao("Os atributos da build devem ser uma lista.")
        resultado = []
        vistos = set()
        for indice, atributo in enumerate(atributos):
            if not isinstance(atributo, dict):
                raise ErroDeValidacao("Cada atributo da build deve conter nome e valor.")
            nome = self._texto(atributo.get("nome"), "O nome do atributo", obrigatorio=True, maximo=80)
            valor = self._texto(atributo.get("valor"), "O valor do atributo", obrigatorio=True, maximo=120)
            chave = self._normalizar_texto(nome)
            if chave in vistos:
                raise ErroDeValidacao("A build não pode repetir o mesmo atributo.")
            vistos.add(chave)
            resultado.append({"nome": nome, "valor": valor, "ordem": indice})
        return resultado

    def _validar_dados_build(self, dados):
        self._validar_objeto(dados)
        jogo = self.obter_jogo(self._inteiro_positivo(dados.get("jogo_id"), "Jogo"))
        nome = self._texto(dados.get("nome_build"), "O nome da build", obrigatorio=True, maximo=120)
        status = dados.get("status") or "planejada"
        if status not in STATUS_BUILD_VALIDOS:
            raise ErroDeValidacao("Status da build inválido.")
        nivel = dados.get("nivel")
        if nivel in (None, ""):
            nivel = None
        else:
            nivel = self._inteiro_nao_negativo({"nivel": nivel}, "nivel", "O nível")
        return {
            "jogo": jogo,
            "nome": nome,
            "descricao": self._texto(dados.get("descricao"), "A descrição") or None,
            "objetivo": self._texto(dados.get("objetivo"), "O objetivo", maximo=160) or None,
            "status": status,
            "nivel": nivel,
            "equipamento": self._texto(dados.get("detalhes_equipamento"), "O equipamento") or None,
            "habilidades": self._texto(dados.get("habilidades"), "As habilidades") or None,
            "observacoes": self._texto(dados.get("observacoes"), "As observações") or None,
            "atributos": self._validar_atributos_build(dados.get("atributos")),
        }

    @staticmethod
    def _aplicar_atributos_build(build, atributos):
        build.atributos = [
            BuildAtributo(nome=item["nome"], valor=item["valor"], ordem=item["ordem"])
            for item in atributos
        ]

    def registrar_build(self, dados):
        valores = self._validar_dados_build(dados)
        build = BuildAnotacao(
            jogo_id=valores["jogo"].id,
            nome_build=valores["nome"],
            descricao=valores["descricao"],
            objetivo=valores["objetivo"],
            status=valores["status"],
            nivel=valores["nivel"],
            detalhes_equipamento=valores["equipamento"],
            habilidades=valores["habilidades"],
            observacoes=valores["observacoes"],
        )
        self._aplicar_atributos_build(build, valores["atributos"])
        db.session.add(build)
        self._registrar_historico(valores["jogo"], "BUILD_CRIADA", f"Build criada: {valores['nome']}")
        db.session.commit()
        return build

    def atualizar_build(self, build_id, dados):
        build = self.obter_build(build_id)
        valores = self._validar_dados_build(dados)
        if build.jogo_id != valores["jogo"].id and RunDiario.query.filter_by(build_id=build.id).first():
            raise ErroDeValidacao("Uma build vinculada a runs não pode ser movida para outro jogo.")
        build.jogo_id = valores["jogo"].id
        build.nome_build = valores["nome"]
        build.descricao = valores["descricao"]
        build.objetivo = valores["objetivo"]
        build.status = valores["status"]
        build.nivel = valores["nivel"]
        build.detalhes_equipamento = valores["equipamento"]
        build.habilidades = valores["habilidades"]
        build.observacoes = valores["observacoes"]
        self._aplicar_atributos_build(build, valores["atributos"])
        self._registrar_historico(valores["jogo"], "BUILD_ATUALIZADA", f"Build atualizada: {valores['nome']}")
        db.session.commit()
        return build

    def excluir_build(self, build_id):
        build = self.obter_build(build_id)
        RunDiario.query.filter_by(build_id=build.id).update({RunDiario.build_id: None})
        db.session.delete(build)
        db.session.commit()

    def listar_desafios(self):
        return (
            Desafio.query.filter_by(usuario_id=self.usuario.id)
            .order_by(Desafio.status.asc(), Desafio.data_limite.asc(), Desafio.id.desc())
            .all()
        )

    def obter_desafio(self, desafio_id):
        desafio = Desafio.query.filter_by(id=desafio_id, usuario_id=self.usuario.id).first()
        if desafio is None:
            raise RecursoNaoEncontrado(f"Desafio {desafio_id} não encontrado para este usuário.")
        return desafio

    def _validar_dados_desafio(self, dados):
        self._validar_objeto(dados)
        jogo = None
        jogo_id = dados.get("jogo_id")
        if jogo_id not in (None, "", 0, "0"):
            jogo = self.obter_jogo(self._inteiro_positivo(jogo_id, "Jogo"))
        tipo = dados.get("tipo") or "personalizado"
        if tipo not in TIPOS_DESAFIO_VALIDOS:
            raise ErroDeValidacao("Tipo de desafio inválido.")
        status = dados.get("status") or "ativo"
        if status not in STATUS_DESAFIO_VALIDOS:
            raise ErroDeValidacao("Status de desafio inválido.")
        data_inicio = self._data_iso(dados.get("data_inicio"), "A data inicial") or date.today()
        data_limite = self._data_iso(dados.get("data_limite"), "A data limite")
        if data_limite and data_limite < data_inicio:
            raise ErroDeValidacao("A data limite não pode ser anterior à data inicial.")
        return {
            "jogo": jogo,
            "titulo": self._texto(dados.get("titulo"), "O título do desafio", obrigatorio=True, maximo=160),
            "descricao": self._texto(dados.get("descricao"), "A descrição") or None,
            "tipo": tipo,
            "meta": self._texto(dados.get("meta"), "A meta", maximo=120) or None,
            "progresso": self._texto(dados.get("progresso"), "O progresso", maximo=120) or None,
            "data_inicio": data_inicio,
            "data_limite": data_limite,
            "status": status,
        }

    def registrar_desafio(self, dados):
        valores = self._validar_dados_desafio(dados)
        desafio = Desafio(
            usuario_id=self.usuario.id,
            jogo_id=valores["jogo"].id if valores["jogo"] else None,
            titulo=valores["titulo"],
            descricao=valores["descricao"],
            tipo=valores["tipo"],
            meta=valores["meta"],
            progresso=valores["progresso"],
            data_inicio=valores["data_inicio"],
            data_limite=valores["data_limite"],
            status=valores["status"],
        )
        db.session.add(desafio)
        if desafio.status == "concluido" and valores["jogo"]:
            self._registrar_historico(valores["jogo"], "DESAFIO_CONCLUIDO", f"Desafio concluído: {desafio.titulo}")
        db.session.commit()
        return desafio

    def atualizar_desafio(self, desafio_id, dados):
        desafio = self.obter_desafio(desafio_id)
        status_anterior = desafio.status
        valores = self._validar_dados_desafio(dados)
        desafio.jogo_id = valores["jogo"].id if valores["jogo"] else None
        desafio.titulo = valores["titulo"]
        desafio.descricao = valores["descricao"]
        desafio.tipo = valores["tipo"]
        desafio.meta = valores["meta"]
        desafio.progresso = valores["progresso"]
        desafio.data_inicio = valores["data_inicio"]
        desafio.data_limite = valores["data_limite"]
        desafio.status = valores["status"]
        if status_anterior != "concluido" and desafio.status == "concluido" and valores["jogo"]:
            self._registrar_historico(valores["jogo"], "DESAFIO_CONCLUIDO", f"Desafio concluído: {desafio.titulo}")
        db.session.commit()
        return desafio

    def excluir_desafio(self, desafio_id):
        desafio = self.obter_desafio(desafio_id)
        db.session.delete(desafio)
        db.session.commit()

    def calcular_estatisticas_dashboard(self):
        jogos = self.listar_jogos()
        total_runs = (
            RunDiario.query.join(Jogo)
            .filter(Jogo.usuario_id == self.usuario.id)
            .count()
        )
        desafios_ativos = (
            Desafio.query.filter_by(usuario_id=self.usuario.id, status="ativo")
            .order_by(Desafio.data_limite.asc(), Desafio.id.desc())
            .limit(5)
            .all()
        )
        quase = sorted(
            [
                jogo
                for jogo in jogos
                if jogo.total_conquistas > 0
                and jogo.conquistas_obtidas < jogo.total_conquistas
                and jogo.conquistas_obtidas * 100 >= jogo.total_conquistas * 70
            ],
            key=lambda jogo: (-jogo.percentual_conquistas, jogo.titulo.casefold()),
        )
        finalizados = [jogo for jogo in jogos if jogo.status in ("zerado", "platinado")]
        notas = [jogo.nota for jogo in jogos if jogo.nota is not None]
        limite = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
        adicionados_30 = sum(1 for jogo in jogos if jogo.criado_em and jogo.criado_em >= limite)
        concluidos_30 = (
            HistoricoJogo.query.join(Jogo)
            .filter(
                Jogo.usuario_id == self.usuario.id,
                HistoricoJogo.tipo.in_(("ZERADO", "PLATINADO")),
                HistoricoJogo.criado_em >= limite,
            )
            .with_entities(HistoricoJogo.jogo_id)
            .distinct()
            .count()
        )
        historico = (
            HistoricoJogo.query.join(Jogo)
            .filter(Jogo.usuario_id == self.usuario.id)
            .order_by(HistoricoJogo.criado_em.desc(), HistoricoJogo.id.desc())
            .limit(6)
            .all()
        )
        pb = (
            RunDiario.query.join(Jogo)
            .filter(Jogo.usuario_id == self.usuario.id, RunDiario.eh_pb.is_(True))
            .order_by(RunDiario.data.desc(), RunDiario.id.desc())
            .first()
        )
        builds = (
            BuildAnotacao.query.join(Jogo)
            .filter(Jogo.usuario_id == self.usuario.id)
            .order_by(BuildAnotacao.id.desc())
            .limit(3)
            .all()
        )
        distribuicao = {status: 0 for status in STATUS_VALIDOS}
        for jogo in jogos:
            distribuicao[jogo.status] += 1
        horas_totais = sum(jogo.tempo_jogado_horas for jogo in jogos)
        total_conquistas = sum(jogo.total_conquistas for jogo in jogos)
        conquistas_obtidas = sum(jogo.conquistas_obtidas for jogo in jogos)
        saude = {
            "total": len(jogos),
            "nunca_iniciados": sum(1 for jogo in jogos if jogo.status == "quero_jogar" and jogo.tempo_jogado_horas == 0),
            "jogando": distribuicao["jogando"],
            "jogados": distribuicao["jogado"],
            "finalizados": len(finalizados),
            "abandonados": distribuicao["abandonado"],
            "favoritos": sum(1 for jogo in jogos if jogo.favorito),
            "quase_concluidos": len(quase),
            "adicionados_30_dias": adicionados_30,
            "concluidos_30_dias": concluidos_30,
        }
        return {
            "total_jogos": len(jogos),
            "jogos_zerados": len(finalizados),
            "jogando": distribuicao["jogando"],
            "horas_totais": horas_totais,
            "nota_media": round(sum(notas) / len(notas), 1) if notas else None,
            "total_runs": total_runs,
            "total_conquistas": total_conquistas,
            "conquistas_obtidas": conquistas_obtidas,
            "favoritos": saude["favoritos"],
            "distribuicao_status": distribuicao,
            "saude": saude,
            "quase_concluidos": [
                {
                    "id": jogo.id,
                    "titulo": jogo.titulo,
                    "obtidas": jogo.conquistas_obtidas,
                    "total": jogo.total_conquistas,
                    "percentual": jogo.percentual_conquistas,
                }
                for jogo in quase[:5]
            ],
            "desafios_ativos": [desafio.to_dict() for desafio in desafios_ativos],
            "historico_recente": [
                {
                    **evento.to_dict(),
                    "titulo_jogo": evento.jogo.titulo,
                }
                for evento in historico
            ],
            "pb_recente": None
            if pb is None
            else {
                "jogo_id": pb.jogo_id,
                "titulo_jogo": pb.jogo.titulo,
                "categoria": pb.categoria,
                "tempo": pb.tempo_formatado,
            },
            "builds_recentes": [
                {
                    "id": build.id,
                    "jogo_id": build.jogo_id,
                    "nome": build.nome_build,
                    "titulo_jogo": build.jogo.titulo,
                    "status": build.status,
                }
                for build in builds
            ],
            "jogando_agora": [jogo.to_dict() for jogo in jogos if jogo.status == "jogando"][:5],
        }
