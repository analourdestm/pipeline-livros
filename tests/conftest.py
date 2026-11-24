import json
from collections import deque
from pathlib import Path

import pytest
import requests

from pipeline_livros import extracao

ORIGEM = "https://books.toscrape.com"
FIXTURES = Path(__file__).parent / "fixtures" / "catalogo"


class TransporteSimulado:
    def __init__(self):
        self.respostas = {
            ORIGEM + "/": (FIXTURES / "index.html").read_bytes(),
            ORIGEM + "/catalogue/page-2.html": (FIXTURES / "page-2.html").read_bytes(),
            ORIGEM + "/catalogue/livro-a_2/index.html": (FIXTURES / "livro-a.html").read_bytes(),
            ORIGEM + "/catalogue/livro-b_1/index.html": (FIXTURES / "livro-b.html").read_bytes(),
        }
        self.chamadas = []

    def get(self, url, **opcoes):
        self.chamadas.append((url, opcoes))
        valor = self.respostas[url]
        if isinstance(valor, deque):
            valor = valor.popleft()
        if isinstance(valor, Exception):
            raise valor
        if isinstance(valor, int):
            return self._resposta(valor, b"")
        return self._resposta(200, valor)

    @staticmethod
    def _resposta(status, corpo):
        resposta = requests.Response()
        resposta.status_code = status
        resposta._content = corpo
        return resposta


@pytest.fixture(autouse=True)
def bloquear_rede(monkeypatch):
    def rejeitar(*args, **kwargs):
        pytest.fail("Uma requisição real foi tentada na suíte offline")

    monkeypatch.setattr(requests.Session, "send", rejeitar)


@pytest.fixture
def catalogo(monkeypatch):
    transporte = TransporteSimulado()
    monkeypatch.setattr(requests.Session, "get", lambda sessao, url, **opcoes: transporte.get(url, **opcoes))
    monkeypatch.setattr(extracao, "esperar", lambda segundos: None)
    return transporte


@pytest.fixture
def inventario():
    return json.loads((FIXTURES / "esperado.json").read_text(encoding="utf-8"))
