import sqlite3
from contextlib import closing

from pipeline_livros.__main__ import main


def linhas_sqlite(diretorio):
    with closing(sqlite3.connect(diretorio / "livros.sqlite3")) as conexao:
        return [list(row) for row in conexao.execute("SELECT * FROM livros ORDER BY url")]


def test_carga_inicial(tmp_path, catalogo, inventario):
    assert main(["--diretorio-saida", str(tmp_path)]) == 0
    assert linhas_sqlite(tmp_path) == inventario["livros"]
    assert [url for url, _ in catalogo.chamadas if url.endswith(("/", "page-2.html"))] == inventario["paginas"]


def test_rejeicao_isolada(tmp_path, catalogo, inventario, caplog):
    catalogo.respostas[inventario["livros"][1][0]] = b"<div class='product_main'><h1>Sem dados</h1></div>"
    assert main(["--diretorio-saida", str(tmp_path)]) == 1
    assert linhas_sqlite(tmp_path) == inventario["livros"][:1]
    assert "preço" in caplog.text


def test_links_equivalentes(tmp_path, catalogo, inventario):
    ultima = inventario["paginas"][-1]
    detalhe = (inventario["livros"][0][0] + "?r=1#livro").encode()
    catalogo.respostas[ultima] = catalogo.respostas[ultima].replace(b"livro-b_1/index.html", detalhe)
    assert main(["--diretorio-saida", str(tmp_path)]) == 0
    assert linhas_sqlite(tmp_path) == inventario["livros"][:1]


def test_catalogo_vazio(tmp_path, catalogo, inventario):
    catalogo.respostas[inventario["paginas"][0]] = b'<h1>All products</h1><form class="form-horizontal"><strong>0</strong> results</form>'
    assert main(["--diretorio-saida", str(tmp_path)]) == 0
    assert linhas_sqlite(tmp_path) == []
