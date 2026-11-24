import sqlite3
from dataclasses import replace

import pytest

from pipeline_livros.armazenamento import ContagensCarga, gravar_livros, ler_livros
from pipeline_livros.transformacao import Livro


def livro(nome):
    return Livro(f"https://books.toscrape.com/catalogue/{nome}_1/index.html", "Título igual", 100, "em estoque", 3)


def test_classifica_apenas_urls_do_lote(tmp_path):
    caminho = tmp_path / "livros.sqlite3"
    a, b, ausente, novo = (livro(nome) for nome in ("a", "b", "c", "d"))
    gravar_livros(caminho, [a, b, ausente])
    alterado = replace(a, preco_pence=201)
    assert gravar_livros(caminho, [alterado, b, novo]) == ContagensCarga(1, 1, 1)
    assert ler_livros(caminho) == [alterado, b, ausente, novo]


def test_lote_interrompido_reverte_alteracao(tmp_path):
    caminho = tmp_path / "livros.sqlite3"
    a, b = livro("a"), livro("b")
    gravar_livros(caminho, [a])
    with pytest.raises(sqlite3.IntegrityError):
        gravar_livros(caminho, [replace(a, preco_pence=101), replace(b, avaliacao=9)])
    assert ler_livros(caminho) == [a]
