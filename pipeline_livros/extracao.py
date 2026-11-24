"""Lê o catálogo público e extrai os campos brutos do HTML."""

import re
from dataclasses import dataclass
from time import sleep as esperar

import requests
from bs4 import BeautifulSoup

from .transformacao import ESTRELAS, URL_CATALOGO, DetalheBruto


class FalhaLeitura(ValueError):
    """Uma página não pôde ser obtida ou interpretada."""


class Leitor:
    def __init__(self, sessao, ao_falhar=None):
        self.sessao = sessao
        self.ao_falhar = ao_falhar

    def ler(self, url):
        for tentativa in range(1, 4):
            try:
                resposta = self.sessao.get(url, timeout=(3.05, 10), allow_redirects=False)
            except requests.exceptions.SSLError as erro:
                raise FalhaLeitura(f"erro de TLS: {erro}") from erro
            except (requests.Timeout, requests.ConnectionError, requests.exceptions.ChunkedEncodingError) as erro:
                if self.ao_falhar is not None:
                    self.ao_falhar(url, tentativa, erro)
                if tentativa == 3:
                    raise FalhaLeitura(f"conexão indisponível após 3 tentativas: {erro}") from erro
                esperar(tentativa)
            except requests.RequestException as erro:
                raise FalhaLeitura(f"erro de requisição: {erro}") from erro
            else:
                if resposta.status_code != 200:
                    causa = " (limite de requisições)" if resposta.status_code == 429 else ""
                    raise FalhaLeitura(f"resposta HTTP {resposta.status_code}{causa}")
                return resposta.content, tentativa - 1


@dataclass
class Listagem:
    links: list[str | None]
    proximo: str | None
    numero: int | None
    ultima: int | None
    total: int | None


def _texto(elemento):
    return elemento.get_text().strip() if elemento is not None else None


def analisar_listagem(html):
    pagina = BeautifulSoup(html, "html.parser")
    if _texto(pagina.select_one("h1")) != "All products":
        raise FalhaLeitura("listagem geral irreconhecível")

    links = []
    for cartao in pagina.select("article.product_pod"):
        ancora = cartao.select_one("h3 a")
        links.append(ancora.get("href") if ancora is not None else None)

    resumo = pagina.select_one("form.form-horizontal")
    total = None
    if resumo is not None:
        quantidade = re.match(r"^([0-9]+) results?\b", resumo.get_text(" ", strip=True))
        if quantidade:
            total = int(quantidade[1])
    if not links and total is None:
        vazio = pagina.find(string=re.compile(r"^\s*No products found\.?(?:\s*)$", re.I))
        if vazio:
            total = 0

    atual = pagina.select_one(".pager .current")
    numero = ultima = None
    if atual is not None:
        marcador = re.fullmatch(r"Page\s+([0-9]+)\s+of\s+([0-9]+)", atual.get_text(" ", strip=True))
        if not marcador:
            raise FalhaLeitura("indicador de paginação inválido")
        numero, ultima = map(int, marcador.groups())

    proximo = None
    if pagina.select_one(".pager .next") is not None:
        ancora = pagina.select_one(".pager .next a")
        proximo = ancora.get("href") if ancora is not None else None
        if not proximo:
            raise FalhaLeitura("link para a próxima página ausente")
    if (not links and total != 0) or (total == 0 and (links or proximo)):
        raise FalhaLeitura("listagem incompleta ou contraditória")
    if numero is not None:
        if not 1 <= numero <= ultima or (numero < ultima) != bool(proximo):
            raise FalhaLeitura("paginação inconsistente")
    elif not proximo and total is None:
        raise FalhaLeitura("fim da listagem sem evidência de cobertura")

    return Listagem(links, proximo, numero, ultima, total)


def analisar_detalhe(html):
    pagina = BeautifulSoup(html, "html.parser")
    detalhe = pagina.select_one(".product_main")
    if detalhe is None:
        raise FalhaLeitura("página de detalhe irreconhecível")
    estrelas = detalhe.select_one(".star-rating")
    tokens = [classe for classe in estrelas.get("class", []) if classe in ESTRELAS] if estrelas else []
    return DetalheBruto(
        _texto(detalhe.select_one("h1")),
        _texto(detalhe.select_one(".price_color")),
        _texto(detalhe.select_one(".availability")),
        tokens[0] if len(tokens) == 1 else None,
    )
