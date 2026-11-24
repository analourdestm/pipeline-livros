from collections import deque
from pathlib import Path
import subprocess
import sys

import pytest
import requests

from pipeline_livros.__main__ import main


@pytest.mark.parametrize("argumentos, codigo, fluxo", [
    (["--help"], 0, "stdout"),
    (["--opcao-invalida"], 2, "stderr"),
])
def test_modulo_com_ajuda_e_sintaxe(tmp_path, argumentos, codigo, fluxo):
    raiz = Path(__file__).parents[2]
    processo = subprocess.run(
        [sys.executable, "-m", "pipeline_livros", *argumentos, "--diretorio-saida", str(tmp_path / "ausente")],
        cwd=raiz, capture_output=True, text=True, check=False,
    )
    assert processo.returncode == codigo
    assert getattr(processo, fluxo)
    assert not list(tmp_path.iterdir())


def test_sucesso_publica_resumo_e_urls(tmp_path, catalogo, inventario, capsys, caplog):
    caplog.set_level("INFO")
    assert main(["--diretorio-saida", str(tmp_path)]) == 0
    saida = capsys.readouterr().out
    for trecho in ("Resultado: sucesso", "Páginas percorridas: 2", "Ocorrências detectadas: 2",
                   "Registros inseridos: 2", "Linhas exportadas: 2", "Total de erros: 0"):
        assert trecho in saida
    urls = [registro.args[0] for registro in caplog.records if registro.msg.startswith("listagem processada")]
    assert urls == inventario["paginas"]


def test_rejeicao_com_saidas_atualizadas(tmp_path, catalogo, inventario, capsys, caplog):
    livro = inventario["livros"][0][0]
    catalogo.respostas[livro] = b"<p>Sem detalhe</p>"
    assert main(["--diretorio-saida", str(tmp_path)]) == 1
    saida = capsys.readouterr().out
    assert "Resultado: conclusão com erros de itens" in saida
    assert "Itens rejeitados: 1" in saida
    assert saida.count("(atualizado)") == 2
    assert livro in caplog.text and "extração" in caplog.text


@pytest.mark.parametrize("transitoria", [True, False])
def test_contagem_de_eventos(tmp_path, catalogo, inventario, capsys, caplog, transitoria):
    pagina = inventario["paginas"][0]
    ultima = catalogo.respostas[pagina] if transitoria else requests.Timeout("teste")
    catalogo.respostas[pagina] = (
        deque([requests.Timeout("teste"), ultima]) if transitoria
        else deque([requests.Timeout("teste"), requests.Timeout("teste"), ultima])
    )
    assert main(["--diretorio-saida", str(tmp_path)]) == (0 if transitoria else 3)
    saida = capsys.readouterr().out
    assert f"Total de erros: {1 if transitoria else 4}" in saida
    assert f"Tentativas de conexão malsucedidas: {1 if transitoria else 3}" in saida
    assert f"Falhas recuperadas: {1 if transitoria else 0}" in saida
    assert f"Erros definitivos: {0 if transitoria else 1}" in saida
    assert caplog.text.count("tentativa ") >= (1 if transitoria else 3)
