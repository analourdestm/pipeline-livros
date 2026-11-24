import csv

from pipeline_livros.armazenamento import gravar_livros, ler_livros
from pipeline_livros.exportacao import exportar_csv
from pipeline_livros.transformacao import Livro


def test_exportacao_csv_para_calc(tmp_path):
    titulos_risco = ["=1+1", "+1+1", "-1+1", "@teste", "＝1+1", "＋1+1", "－1+1", "＠teste"]
    comum = 'Café, "livros" e histórias'
    titulos = titulos_risco + [comum]
    livros = [
        Livro(f"https://books.toscrape.com/catalogue/sintetico_{i}/index.html", titulo, 1234, "sem estoque", 5)
        for i, titulo in enumerate(titulos)
    ]
    banco = tmp_path / "livros.sqlite3"
    csv_sintetico = tmp_path / "livros.csv"
    gravar_livros(banco, livros)
    assert exportar_csv(csv_sintetico, ler_livros(banco)) == len(livros)
    assert ler_livros(banco) == livros

    with csv_sintetico.open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.reader(arquivo))
    assert linhas[0] == ["titulo", "preco_gbp", "disponibilidade", "avaliacao", "url"]
    esperados = ["'" + titulo for titulo in titulos_risco] + [comum]
    assert linhas[1:] == [
        [titulo, "12.34", "sem estoque", "5", livro.url]
        for titulo, livro in zip(esperados, livros, strict=True)
    ]
    print(f"CSV sintético para o Calc: {csv_sintetico}")
