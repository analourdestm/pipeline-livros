from collections import deque
import sqlite3

import pytest
import requests

from pipeline_livros import pipeline
from pipeline_livros.armazenamento import ler_livros


def arquivos(diretorio):
    return ((diretorio / "livros.sqlite3").read_bytes(), (diretorio / "livros.csv").read_bytes())


@pytest.mark.parametrize("tipo", ["lista", "detalhe"])
@pytest.mark.parametrize("tentativa", [2, 3])
def test_recuperacao_em_listagem_e_detalhe(tmp_path, catalogo, inventario, tipo, tentativa):
    url = inventario["paginas"][1] if tipo == "lista" else inventario["livros"][0][0]
    catalogo.respostas[url] = deque([requests.Timeout("teste")] * (tentativa - 1) + [catalogo.respostas[url]])
    resultado = pipeline.executar(tmp_path)
    assert resultado.codigo == 0
    assert resultado.falhas_recuperadas == resultado.tentativas_malsucedidas == tentativa - 1
    assert resultado.erros_definitivos == 0


@pytest.mark.parametrize("tipo", ["conexao", "ciclo", "interrompida", "externa"])
def test_falha_cobertura_preserva_ambas_saidas(tmp_path, catalogo, inventario, tipo):
    assert pipeline.executar(tmp_path).codigo == 0
    anterior = arquivos(tmp_path)
    inicio, segunda = inventario["paginas"]
    if tipo == "conexao":
        catalogo.respostas[segunda] = deque([requests.Timeout("teste")] * 3)
    elif tipo == "ciclo":
        catalogo.respostas[inicio] = catalogo.respostas[inicio].replace(b"catalogue/page-2.html", b"/index.html")
    elif tipo == "externa":
        catalogo.respostas[inicio] = catalogo.respostas[inicio].replace(b"catalogue/page-2.html", b"https://fora.example/")
    else:
        catalogo.respostas[inicio] = catalogo.respostas[inicio].split(b'<li class="next">')[0] + b"</ul>"
    resultado = pipeline.executar(tmp_path)
    assert resultado.codigo == 3 and resultado.etapa_falha == "cobertura"
    assert resultado.carga.inseridos == resultado.linhas_exportadas == 0
    assert (resultado.estado_banco, resultado.estado_csv) == ("preservado", "preservado")
    assert arquivos(tmp_path) == anterior


def test_tres_falhas_no_detalhe_retem_o_livro(tmp_path, catalogo, inventario):
    assert pipeline.executar(tmp_path).codigo == 0
    livro = inventario["livros"][0][0]
    catalogo.respostas[livro] = deque([requests.Timeout("teste")] * 3)
    resultado = pipeline.executar(tmp_path)
    assert resultado.codigo == 1 and resultado.rejeitados == 1
    assert resultado.tentativas_malsucedidas == 3 and resultado.erros_definitivos == 1
    assert resultado.carga.mantidos == 1 and resultado.linhas_exportadas == 2
    assert ler_livros(tmp_path / "livros.sqlite3")[0].preco_pence == 1234


@pytest.mark.parametrize("carregada", [True, False])
def test_falha_de_qualidade_preserva_ausencia_ou_saidas(tmp_path, catalogo, inventario, carregada):
    if carregada:
        assert pipeline.executar(tmp_path).codigo == 0
        anterior = arquivos(tmp_path)
    for url, *_ in inventario["livros"]:
        catalogo.respostas[url] = 404
    resultado = pipeline.executar(tmp_path)
    assert resultado.codigo == 3 and resultado.etapa_falha == "qualidade dos dados"
    assert resultado.rejeitados == 2 and resultado.linhas_exportadas == 0
    if carregada:
        assert arquivos(tmp_path) == anterior
    else:
        assert not resultado.banco.exists() and not resultado.csv.exists()


def test_falha_de_gravacao_preserva_ambas_saidas(tmp_path, catalogo, monkeypatch):
    assert pipeline.executar(tmp_path).codigo == 0
    anterior = arquivos(tmp_path)

    def falhar(*args):
        raise sqlite3.OperationalError("escrita simulada")

    monkeypatch.setattr(pipeline, "gravar_livros", falhar)
    resultado = pipeline.executar(tmp_path)
    assert resultado.codigo == 3 and resultado.etapa_falha == "armazenamento"
    assert resultado.carga.atualizados == resultado.linhas_exportadas == 0
    assert arquivos(tmp_path) == anterior


@pytest.mark.parametrize("tem_csv", [True, False])
def test_falha_de_csv_mantem_banco_atualizado(tmp_path, catalogo, inventario, monkeypatch, tem_csv):
    if tem_csv:
        assert pipeline.executar(tmp_path).codigo == 0
        csv_anterior = (tmp_path / "livros.csv").read_bytes()
    url = inventario["livros"][0][0]
    catalogo.respostas[url] = catalogo.respostas[url].replace(b"12.34", b"25.00")

    def falhar(*args):
        raise OSError("exportação simulada")

    monkeypatch.setattr(pipeline, "exportar_csv", falhar)
    resultado = pipeline.executar(tmp_path)
    assert resultado.codigo == 3 and resultado.etapa_falha == "exportação"
    assert resultado.estado_banco == "atualizado"
    assert resultado.estado_csv == ("desatualizado" if tem_csv else "ausente")
    assert resultado.linhas_exportadas == 0
    assert ler_livros(resultado.banco)[0].preco_pence == 2500
    if tem_csv:
        assert resultado.csv.read_bytes() == csv_anterior
    else:
        assert not resultado.csv.exists()


def test_destino_ocupado_preserva_saidas(tmp_path, catalogo):
    assert pipeline.executar(tmp_path).codigo == 0
    anteriores = arquivos(tmp_path)
    chamadas = len(catalogo.chamadas)
    with pipeline.bloquear_destino(tmp_path):
        resultado = pipeline.executar(tmp_path)
    assert resultado.codigo == 3 and resultado.etapa_falha == "preparação"
    assert arquivos(tmp_path) == anteriores
    assert len(catalogo.chamadas) == chamadas
