# Pipeline de livros

Pipeline Python local para coletar e tratar o catálogo público [Books to Scrape](https://books.toscrape.com/).

## Configuração no macOS

Instale gratuitamente o [Python 3.14.x](https://www.python.org/downloads/macos/) e rode na raiz do repositório:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install '.[dev]'
```

## Carga local

Com internet e permissão de gravação no destino:

```sh
python -m pipeline_livros --help
python -m pipeline_livros --diretorio-saida saida
python -m sqlite3 saida/livros.sqlite3 'SELECT titulo, preco_pence FROM livros ORDER BY url LIMIT 5'
```

O preço no SQLite é armazenado em pence. Por exemplo, 1234 representa 12,34 libras.

## Testes

Com as dependências já instaladas, a suíte roda sem internet:

```sh
python -m pytest
```

## Arquivos e resultado

O diretório padrão `saida/` recebe `livros.sqlite3` e `livros.csv`. O CSV contém a base confirmada, inclusive os últimos valores válidos dos livros que estiverem ausentes ou forem rejeitados em uma nova coleta. O SQLite guarda o título padronizado e o preço em pence inteiros. O CSV apresenta o preço em libras com ponto decimal e duas casas.

O resumo na saída padrão mostra o estado das duas saídas, a cobertura e as contagens. O total de erros soma as tentativas de conexão malsucedidas e os desfechos definitivos. Falhas recuperadas são um subconjunto das tentativas malsucedidas. Os diagnósticos aparecem na saída de erro.

| Código | Resultado |
| --- | --- |
| 0 | Sucesso |
| 1 | Conclusão com erros de itens, com SQLite e CSV atualizados |
| 2 | Argumentos inválidos |
| 3 | Falha de preparação, cobertura, qualidade, armazenamento ou exportação |

Falhas de cobertura, qualidade ou armazenamento preservam os arquivos anteriores. Se apenas a exportação falhar, o SQLite confirmado fica disponível e o CSV anterior, quando existente, é indicado como desatualizado.

## Abrir o CSV no LibreOffice Calc

No [LibreOffice Calc](https://www.libreoffice.org/download/), abra o arquivo como Texto CSV. Selecione UTF-8, vírgula e aspas duplas. Defina a coluna `titulo` como **Texto** e desative **Avaliar fórmulas**. Para importar o preço como número com ponto decimal, use a localidade Inglês (EUA) para a coluna ou para a importação. O exportador acrescenta um apóstrofo aos títulos de risco no CSV, preservando o título padronizado no SQLite.

O [guia de validação](specs/001-coletar-catalogo-livros/quickstart.md) descreve a suíte offline, a coleta pública e o teste sintético para o Calc.

## Dependências

| Dependência | Finalidade | Versão testada |
| --- | --- | --- |
| CPython | Execução e bibliotecas nativas, incluindo SQLite, CSV e logging | 3.14.6 |
| Requests | Requisições HTTP | 2.34.2 |
| Beautiful Soup | Extração de campos do HTML com `html.parser` | 4.15.0 |
| Pytest | Testes automatizados de desenvolvimento | 9.2.0 |
| Setuptools | Construção do pacote pelo `pip` | 83.0.0 |
| LibreOffice Calc | Verificação dos títulos no CSV | 26.8.3.1 |

As ferramentas do pipeline e de validação são gratuitas.
