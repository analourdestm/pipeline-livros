"""Converte os campos brutos em livros com valores padronizados."""

import re
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urljoin, urlsplit

HOST_CATALOGO = "books.toscrape.com"
URL_CATALOGO = f"https://{HOST_CATALOGO}/"
ROTA_DETALHE = re.compile(r"/catalogue/[a-zA-Z0-9_-]+/index\.html")
ROTA_LISTAGEM = re.compile(r"/catalogue/page-[1-9][0-9]*\.html")
ESTRELAS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
MAX_PENCE = 2**63 - 1


@dataclass(frozen=True)
class DetalheBruto:
    titulo: str | None
    preco: str | None
    disponibilidade: str | None
    avaliacao: str | None


@dataclass(frozen=True)
class Livro:
    url: str
    titulo: str
    preco_pence: int
    disponibilidade: str
    avaliacao: int


def normalizar_url(base, link, *, detalhe=True):
    """Resolve o link e restringe o destino às rotas HTTPS do catálogo."""
    if not link or not link.strip() or any(ord(c) < 32 for c in link):
        raise ValueError("link ausente ou inválido")
    try:
        partes = urlsplit(urljoin(base, link.strip()))
        porta = partes.port
    except ValueError as erro:
        raise ValueError("link inválido") from erro
    if (
        partes.scheme != "https" or partes.hostname != HOST_CATALOGO
        or porta not in (None, 443) or partes.username is not None
    ):
        raise ValueError("link fora da origem HTTPS do catálogo")

    caminho = partes.path or "/"
    if detalhe:
        if not ROTA_DETALHE.fullmatch(caminho):
            raise ValueError("link fora das rotas de detalhe do catálogo")
    elif caminho in ("/", "/index.html", "/catalogue/page-1.html"):
        caminho = "/"
    elif not ROTA_LISTAGEM.fullmatch(caminho):
        raise ValueError("link fora das rotas de listagem do catálogo")
    return f"https://{HOST_CATALOGO}{caminho}"


def _preco_em_pence(texto):
    if not texto or not re.fullmatch(r"£[0-9]+\.[0-9]{2}", texto.strip()):
        raise ValueError("preço ausente ou inválido em GBP")
    valor = Decimal(texto.strip()[1:]) * 100
    if valor > MAX_PENCE:
        raise ValueError("preço fora do intervalo do SQLite")
    return int(valor)


def _disponibilidade(texto):
    texto = " ".join((texto or "").lower().split())
    estoque = re.fullmatch(r"in stock(?: \(([0-9]+) available\))?", texto)
    if estoque and (estoque[1] is None or estoque[1].lstrip("0")):
        return "em estoque"
    if re.fullmatch(r"out of stock(?: \(0+ available\))?|0+ available", texto):
        return "sem estoque"
    raise ValueError("disponibilidade ausente, desconhecida ou contraditória")


def tratar_livro(url, detalhe):
    url = normalizar_url(URL_CATALOGO, url)
    titulo = (detalhe.titulo or "").strip()
    if not titulo:
        raise ValueError("título ausente ou vazio")
    preco = _preco_em_pence(detalhe.preco)
    disponibilidade = _disponibilidade(detalhe.disponibilidade)
    avaliacao = ESTRELAS.get(detalhe.avaliacao)
    if avaliacao is None:
        raise ValueError("avaliação ausente ou inválida")
    return Livro(url, titulo, preco, disponibilidade, avaliacao)
