import csv

import pytest

from pipeline_livros import exportacao
from pipeline_livros.transformacao import Livro


def livro(slug, titulo, preco):
    return Livro(f"https://books.toscrape.com/catalogue/{slug}_1/index.html", titulo, preco, "em estoque", 4)


def ler_csv(caminho):
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.reader(arquivo))


def test_formato_e_substituicao(tmp_path):
    destino = tmp_path / "livros.csv"
    destino.write_bytes(b"anterior")
    a = livro("a", 'Café, "livros"\ne histórias', 1234)
    b = livro("b", "Outro", 0)
    assert exportacao.exportar_csv(destino, [b, a]) == 2
    assert ler_csv(destino) == [
        ["titulo", "preco_gbp", "disponibilidade", "avaliacao", "url"],
        [a.titulo, "12.34", "em estoque", "4", a.url],
        [b.titulo, "0.00", "em estoque", "4", b.url],
    ]
    assert destino.read_bytes().endswith(b"\r\n")
    assert exportacao.exportar_csv(destino, []) == 0
    assert len(ler_csv(destino)) == 1


@pytest.mark.parametrize("simular", ["preparacao", "publicacao"])
def test_preserva_csv_e_limpa_temporario(tmp_path, monkeypatch, simular):
    destino = tmp_path / "livros.csv"
    original = b"anterior"
    destino.write_bytes(original)

    def falhar(*args, **kwargs):
        raise OSError("falha de gravação simulada")

    if simular == "preparacao":
        monkeypatch.setattr(exportacao.csv, "writer", falhar)
    else:
        monkeypatch.setattr(exportacao.os, "replace", falhar)
    with pytest.raises(OSError, match="simulada"):
        exportacao.exportar_csv(destino, [livro("a", "A", 100)])
    assert destino.read_bytes() == original
    assert list(tmp_path.iterdir()) == [destino]
