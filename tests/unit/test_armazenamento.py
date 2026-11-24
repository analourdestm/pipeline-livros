import sqlite3

import pytest

from pipeline_livros.armazenamento import gravar_livros, ler_livros
from pipeline_livros.transformacao import Livro


def test_carga_inicial_e_consulta_ordenada(tmp_path):
    destino = tmp_path / "livros.sqlite3"
    a = Livro("https://books.toscrape.com/catalogue/a_2/index.html", "A", 0, "em estoque", 5)
    b = Livro("https://books.toscrape.com/catalogue/b_1/index.html", "B", 301, "sem estoque", 1)
    assert gravar_livros(destino, [b, a]).inseridos == 2
    assert ler_livros(destino) == [a, b]


@pytest.mark.parametrize("valores", [
    ("", 100, "em estoque", 3), ("A", -1, "em estoque", 3),
    ("A", 100, "desconhecido", 3), ("A", 100, "em estoque", 6),
    ("A", None, "em estoque", 3),
])
def test_restricao_impede_publicacao_inicial(tmp_path, valores):
    destino = tmp_path / "livros.sqlite3"
    livro = Livro("https://books.toscrape.com/catalogue/a_1/index.html", *valores)
    with pytest.raises(sqlite3.IntegrityError):
        gravar_livros(destino, [livro])
    assert not list(tmp_path.iterdir())
