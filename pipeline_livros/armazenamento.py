"""Mantém os livros tratados no SQLite local."""

import os
import sqlite3
from contextlib import closing
from dataclasses import astuple, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from .transformacao import Livro

CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS livros (
    url TEXT PRIMARY KEY NOT NULL,
    titulo TEXT NOT NULL CHECK (length(trim(titulo)) > 0),
    preco_pence INTEGER NOT NULL CHECK (preco_pence >= 0),
    disponibilidade TEXT NOT NULL CHECK (disponibilidade IN ('em estoque', 'sem estoque')),
    avaliacao INTEGER NOT NULL CHECK (avaliacao BETWEEN 1 AND 5)
) STRICT
"""
COLUNAS = "url, titulo, preco_pence, disponibilidade, avaliacao"
INSERIR = f"INSERT INTO livros ({COLUNAS}) VALUES (?, ?, ?, ?, ?)"
ATUALIZAR = "UPDATE livros SET titulo = ?, preco_pence = ?, disponibilidade = ?, avaliacao = ? WHERE url = ?"


@dataclass
class ContagensCarga:
    inseridos: int = 0
    atualizados: int = 0
    mantidos: int = 0


def _gravar(caminho, livros):
    contagens = ContagensCarga()
    with closing(sqlite3.connect(caminho, autocommit=False)) as conexao:
        with conexao:
            conexao.execute(CRIAR_TABELA)
            for livro in livros:
                valores = astuple(livro)
                anterior = conexao.execute(
                    f"SELECT {COLUNAS} FROM livros WHERE url = ?", (livro.url,)
                ).fetchone()
                if anterior is None:
                    conexao.execute(INSERIR, valores)
                    contagens.inseridos += 1
                elif anterior == valores:
                    contagens.mantidos += 1
                else:
                    conexao.execute(ATUALIZAR, (*valores[1:], livro.url))
                    contagens.atualizados += 1
    return contagens


def gravar_livros(caminho, livros):
    if caminho.exists():
        return _gravar(caminho, livros)

    with NamedTemporaryFile(dir=caminho.parent, suffix=".sqlite3.tmp", delete=False) as arquivo:
        temporario = Path(arquivo.name)
    try:
        contagens = _gravar(temporario, livros)
        os.replace(temporario, caminho)
        return contagens
    finally:
        temporario.unlink(missing_ok=True)


def ler_livros(caminho):
    uri = caminho.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conexao:
        linhas = conexao.execute(f"SELECT {COLUNAS} FROM livros ORDER BY url")
        return [Livro(*linha) for linha in linhas]
