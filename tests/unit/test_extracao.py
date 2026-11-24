from collections import deque

import pytest
import requests

from pipeline_livros.extracao import URL_CATALOGO, FalhaLeitura, Leitor, analisar_detalhe, analisar_listagem


def test_paginas_e_campos_brutos(catalogo):
    with requests.Session() as sessao:
        leitor = Leitor(sessao)
        primeira = analisar_listagem(leitor.ler(URL_CATALOGO)[0])
        pagina2 = "https://books.toscrape.com/catalogue/page-2.html"
        ultima = analisar_listagem(leitor.ler(pagina2)[0])
        detalhe = analisar_detalhe(leitor.ler(pagina2.replace("page-2.html", "livro-a_2/index.html"))[0])
    assert (primeira.numero, primeira.ultima, primeira.total) == (1, 2, 2)
    assert primeira.proximo == "catalogue/page-2.html"
    assert (ultima.numero, ultima.ultima, ultima.proximo) == (2, 2, None)
    assert (detalhe.titulo, detalhe.preco, detalhe.avaliacao) == ("Café e livros", "£12.34", "Four")
    assert catalogo.chamadas[0][1] == {"timeout": (3.05, 10), "allow_redirects": False}


def test_vazio_explicito_e_cartao_sem_link():
    vazio = b'<h1>All products</h1><form class="form-horizontal"><strong>0</strong> results</form>'
    assert analisar_listagem(vazio).total == 0
    pagina = b'<h1>All products</h1><form class="form-horizontal"><strong>1</strong> result</form><article class="product_pod"></article>'
    assert analisar_listagem(pagina).links == [None]


def test_preserva_espacos_do_titulo_com_marcacao():
    html = b'<div class="product_main"><h1>A <em>Book</em> of Stories</h1></div>'
    assert analisar_detalhe(html).titulo == "A Book of Stories"


@pytest.mark.parametrize("html", [
    b"<h1>Erro</h1>",
    b"<h1>All products</h1>",
    b'<h1>All products</h1><ul class="pager"><li class="current">Page 1 of 2</li></ul>',
])
def test_listagem_invalida(html):
    with pytest.raises(FalhaLeitura):
        analisar_listagem(html)


def test_http_permanente_sem_repetir(catalogo):
    catalogo.respostas[URL_CATALOGO] = 302
    with requests.Session() as sessao, pytest.raises(FalhaLeitura, match="302"):
        Leitor(sessao).ler(URL_CATALOGO)
    assert len(catalogo.chamadas) == 1


@pytest.mark.parametrize("recuperar", [True, False])
def test_limite_de_tres_tentativas(catalogo, recuperar):
    ultima = catalogo.respostas[URL_CATALOGO] if recuperar else requests.Timeout()
    catalogo.respostas[URL_CATALOGO] = deque([requests.Timeout(), requests.ConnectionError(), ultima])
    falhas = []
    with requests.Session() as sessao:
        leitor = Leitor(sessao, lambda url, tentativa, erro: falhas.append(tentativa))
        if recuperar:
            assert leitor.ler(URL_CATALOGO)[1] == 2
        else:
            with pytest.raises(FalhaLeitura, match="3 tentativas"):
                leitor.ler(URL_CATALOGO)
    assert len(catalogo.chamadas) == 3
    assert falhas == ([1, 2] if recuperar else [1, 2, 3])


def test_origem_e_rotas_externas_recusadas(catalogo):
    from pipeline_livros.transformacao import normalizar_url

    for link in ("http://books.toscrape.com/", "//outra.example/", "/catalogue/category/books/", "https://a@books.toscrape.com/"):
        with pytest.raises(ValueError):
            normalizar_url(URL_CATALOGO, link, detalhe=False)
    assert not catalogo.chamadas
