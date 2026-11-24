import csv
from collections import deque
from dataclasses import astuple

from pipeline_livros.armazenamento import ContagensCarga, ler_livros
from pipeline_livros.pipeline import executar


def test_reprocessar_identico_e_atualizar(tmp_path, catalogo, inventario):
    url = inventario["livros"][0][0]
    caminho = tmp_path / "livros.sqlite3"
    assert executar(tmp_path).carga == ContagensCarga(2, 0, 0)
    assert executar(tmp_path).carga == ContagensCarga(0, 0, 2)

    catalogo.respostas[url] = catalogo.respostas[url].replace(b"12.34", b"20.00")
    assert executar(tmp_path).carga == ContagensCarga(0, 1, 1)
    esperado = inventario["livros"]
    esperado[0][2] = 2000
    assert [list(astuple(livro)) for livro in ler_livros(caminho)] == esperado


def test_primeira_ocorrencia_valida_e_retencao(tmp_path, catalogo, inventario):
    assert executar(tmp_path).codigo == 0
    primeira, segunda = inventario["paginas"]
    url_a, url_b = [linha[0] for linha in inventario["livros"]]
    detalhe_a = catalogo.respostas[url_a]
    catalogo.respostas[primeira] = catalogo.respostas[primeira].replace(b"2</strong> results", b"3</strong> results")
    catalogo.respostas[segunda] = catalogo.respostas[segunda].replace(b"2</strong> results", b"3</strong> results")
    catalogo.respostas[segunda] = catalogo.respostas[segunda].replace(
        b'<article class="product_pod"><h3><a href="livro-b_1/index.html">Outro livro</a></h3></article>',
        f'<article class="product_pod"><h3><a href="{url_a}">A</a></h3></article>'
        f'<article class="product_pod"><h3><a href="{url_a}">A</a></h3></article>'.encode(),
    )
    catalogo.respostas[url_a] = deque([
        b"<div class='product_main'><h1>Invalido</h1></div>",
        detalhe_a.replace(b"12.34", b"20.00"),
        detalhe_a.replace(b"12.34", b"30.00"),
    ])
    resultado = executar(tmp_path)
    assert resultado.rejeitados == resultado.duplicatas == 1
    assert resultado.carga == ContagensCarga(0, 1, 0)
    livros = {livro.url: livro for livro in ler_livros(tmp_path / "livros.sqlite3")}
    assert livros[url_a].preco_pence == 2000
    assert livros[url_b].preco_pence == 0


def test_publicacao_e_catalogo_explicitamente_vazio(tmp_path, catalogo, inventario):
    saida = tmp_path / "livros.csv"
    assert executar(tmp_path).linhas_exportadas == 2
    catalogo.respostas[inventario["livros"][0][0]] = catalogo.respostas[inventario["livros"][0][0]].replace(b"12.34", b"20.00")
    assert executar(tmp_path).linhas_exportadas == 2
    with saida.open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.reader(arquivo))
    assert len(linhas) == 3
    assert linhas[1][1] == "20.00"
    assert [linha[-1] for linha in linhas[1:]] == [livro[0] for livro in inventario["livros"]]

    catalogo.respostas[inventario["paginas"][0]] = b'<h1>All products</h1><form class="form-horizontal"><strong>0</strong> results</form>'
    anterior = saida.read_bytes()
    assert executar(tmp_path).linhas_exportadas == 2
    assert saida.read_bytes() == anterior

    destino_novo = tmp_path / "vazio"
    resultado = executar(destino_novo)
    assert resultado.codigo == 0 and resultado.csv_publicado and resultado.linhas_exportadas == 0
    assert len((destino_novo / "livros.csv").read_bytes().splitlines()) == 1
