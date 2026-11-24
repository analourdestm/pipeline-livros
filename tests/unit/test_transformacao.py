from dataclasses import replace

import pytest

from pipeline_livros.transformacao import DetalheBruto, Livro, normalizar_url, tratar_livro

ORIGEM = "https://books.toscrape.com/"
URL = ORIGEM + "catalogue/livro_1/index.html"
DETALHE = DetalheBruto("  Café e livros  ", "£12.34", "In stock (3 available)", "Four")


def test_livro_padronizado():
    assert tratar_livro(URL, DETALHE) == Livro(URL, "Café e livros", 1234, "em estoque", 4)
    assert tratar_livro(URL, replace(DETALHE, disponibilidade="Out of stock")).disponibilidade == "sem estoque"
    assert tratar_livro(URL, replace(DETALHE, disponibilidade="Out of stock (0 available)")).disponibilidade == "sem estoque"
    assert tratar_livro(URL, replace(DETALHE, disponibilidade="0 available")).disponibilidade == "sem estoque"


@pytest.mark.parametrize("campo, valor", [
    ("titulo", None), ("titulo", " \t"), ("preco", "$1.00"), ("preco", "£1.234"),
    ("preco", "£-1.00"), ("preco", "£92233720368547758.08"), ("avaliacao", "Six"),
    ("disponibilidade", None), ("disponibilidade", "Indefinido"),
    ("disponibilidade", "In stock (0 available)"), ("disponibilidade", "Out of stock (2 available)"),
])
def test_rejeita_campos_invalidos(campo, valor):
    with pytest.raises(ValueError):
        tratar_livro(URL, replace(DETALHE, **{campo: valor}))


def test_identidade_de_url():
    assert normalizar_url(ORIGEM, "catalogue/livro_1/index.html") == URL
    assert normalizar_url(ORIGEM, "https://BOOKS.TOSCRAPE.COM:443/catalogue/livro_1/index.html?r=1#detalhe") == URL
    with pytest.raises(ValueError):
        normalizar_url(ORIGEM, "//books.toscrape.com.example/catalogue/livro_1/index.html")
