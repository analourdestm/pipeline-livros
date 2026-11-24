"""Gera o CSV completo e publica apenas o arquivo terminado."""

import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

CABECALHO = ("titulo", "preco_gbp", "disponibilidade", "avaliacao", "url")
INICIOS_DE_FORMULA = "=+-@＝＋－＠\t\r\n"


def _linha(livro):
    titulo = livro.titulo
    if titulo and titulo[0] in INICIOS_DE_FORMULA:
        titulo = "'" + titulo
    libras, pence = divmod(livro.preco_pence, 100)
    return titulo, f"{libras}.{pence:02d}", livro.disponibilidade, livro.avaliacao, livro.url


def exportar_csv(caminho, livros):
    temporario = None
    try:
        with NamedTemporaryFile(
            mode="w", dir=caminho.parent, suffix=".csv.tmp",
            encoding="utf-8", newline="", delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            escritor = csv.writer(arquivo)
            escritor.writerow(CABECALHO)
            ordenados = sorted(livros, key=lambda livro: livro.url)
            escritor.writerows(_linha(livro) for livro in ordenados)
        os.replace(temporario, caminho)
        return len(ordenados)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)
