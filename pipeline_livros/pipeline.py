"""Orquestra a execução e protege o diretório de saída."""

import fcntl
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import requests

from .armazenamento import ContagensCarga, gravar_livros, ler_livros
from .exportacao import exportar_csv
from .extracao import FalhaLeitura, Leitor, analisar_detalhe, analisar_listagem
from .transformacao import URL_CATALOGO, normalizar_url, tratar_livro

logger = logging.getLogger(__name__)


@contextmanager
def bloquear_destino(diretorio):
    diretorio.mkdir(parents=True, exist_ok=True)
    with (diretorio / ".pipeline.lock").open("a", encoding="utf-8") as arquivo:
        fcntl.flock(arquivo, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


@dataclass
class Resultado:
    banco: Path
    csv: Path
    paginas: int = 0
    detectados: int = 0
    rejeitados: int = 0
    duplicatas: int = 0
    carga: ContagensCarga = field(default_factory=ContagensCarga)
    linhas_exportadas: int = 0
    banco_gravado: bool = False
    csv_publicado: bool = False
    etapa_falha: str | None = None
    tentativas_malsucedidas: int = 0
    falhas_recuperadas: int = 0
    erros_definitivos: int = 0

    @property
    def codigo(self):
        if self.etapa_falha:
            return 3
        return 1 if self.rejeitados else 0

    @property
    def total_erros(self):
        return self.tentativas_malsucedidas + self.erros_definitivos

    @property
    def estado_banco(self):
        if self.banco_gravado:
            return "atualizado"
        return "preservado" if self.banco.is_file() else "ausente"

    @property
    def estado_csv(self):
        if self.csv_publicado:
            return "atualizado"
        if not self.csv.is_file():
            return "ausente"
        return "desatualizado" if self.banco_gravado else "preservado"

    def registrar_erro(self, etapa, contexto, causa):
        self.erros_definitivos += 1
        logger.error("%s | %s | %s", etapa, contexto, causa)

    def registrar_tentativa(self, url, tentativa, causa):
        self.tentativas_malsucedidas += 1
        logger.warning("extração | %s | tentativa %d malsucedida: %s", url, tentativa, causa)

    def falhar(self, etapa, contexto, causa):
        self.etapa_falha = etapa
        self.registrar_erro(etapa, contexto, causa)


def _coletar(leitor, resultado):
    livros = {}
    visitadas = set()
    url = URL_CATALOGO
    total = ultima = None

    while url:
        try:
            if url in visitadas:
                raise FalhaLeitura("ciclo de paginação")
            html, recuperadas = leitor.ler(url)
            pagina = analisar_listagem(html)
            resultado.falhas_recuperadas += recuperadas
            numero = len(visitadas) + 1
            if pagina.numero is not None and pagina.numero != numero:
                raise FalhaLeitura("sequência de páginas interrompida")
            if pagina.ultima is not None:
                if ultima is not None and pagina.ultima != ultima:
                    raise FalhaLeitura("última página inconsistente")
                ultima = pagina.ultima
            if pagina.total is not None:
                if total is not None and pagina.total != total:
                    raise FalhaLeitura("total de ocorrências inconsistente")
                total = pagina.total
            if ultima is not None and bool(pagina.proximo) != (numero < ultima):
                raise FalhaLeitura("fim da paginação inconsistente")
            proxima = normalizar_url(url, pagina.proximo, detalhe=False) if pagina.proximo else None
        except ValueError as erro:
            resultado.falhar("cobertura", url, erro)
            return livros

        visitadas.add(url)
        resultado.paginas += 1
        resultado.detectados += len(pagina.links)
        logger.info("listagem processada | extração | %s", url)
        for link in pagina.links:
            contexto = url
            etapa = "extração"
            try:
                contexto = normalizar_url(url, link)
                html, recuperadas = leitor.ler(contexto)
                bruto = analisar_detalhe(html)
                resultado.falhas_recuperadas += recuperadas
                etapa = "transformação"
                livro = tratar_livro(contexto, bruto)
            except ValueError as erro:
                resultado.rejeitados += 1
                resultado.registrar_erro(etapa, contexto, f"livro rejeitado: {erro}")
            else:
                if livro.url in livros:
                    resultado.duplicatas += 1
                else:
                    livros[livro.url] = livro
        url = proxima

    if total is not None and resultado.detectados != total:
        resultado.falhar("cobertura", URL_CATALOGO, "ocorrências detectadas diferem do total anunciado")
    elif resultado.detectados and not livros:
        resultado.falhar("qualidade dos dados", URL_CATALOGO, "todos os livros foram rejeitados")
    return livros


def executar(diretorio):
    resultado = Resultado(diretorio / "livros.sqlite3", diretorio / "livros.csv")
    try:
        with bloquear_destino(diretorio):
            with requests.Session() as sessao:
                livros = _coletar(Leitor(sessao, resultado.registrar_tentativa), resultado)
            if resultado.etapa_falha:
                return resultado
            try:
                resultado.carga = gravar_livros(resultado.banco, livros.values())
                resultado.banco_gravado = True
            except (OSError, sqlite3.Error) as erro:
                resultado.falhar("armazenamento", resultado.banco, erro)
                return resultado
            try:
                resultado.linhas_exportadas = exportar_csv(resultado.csv, ler_livros(resultado.banco))
                resultado.csv_publicado = True
            except (OSError, sqlite3.Error) as erro:
                resultado.falhar("exportação", resultado.csv, erro)
    except OSError as erro:
        resultado.falhar("preparação", diretorio, erro)
    return resultado
