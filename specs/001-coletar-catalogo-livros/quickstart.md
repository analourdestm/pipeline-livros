# Guia de validação — Pipeline de livros

Este guia define os comandos e resultados esperados para quando a implementação estiver disponível. Execute os comandos na raiz do repositório em um terminal do macOS.

## Preparar o ambiente

Instale o [CPython 3.14.x do Python.org](https://www.python.org/downloads/macos/). Use o [LibreOffice Calc](https://www.libreoffice.org/download/download-libreoffice/) na verificação manual do CSV.

```sh
python3.14 --version
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install '.[dev]'
```

A instalação inicial requer acesso às fontes das dependências. Depois dela, a suíte local pode rodar sem internet.

## Testes locais

```sh
python -m pytest
```

A suíte usa um catálogo de referência com mais de uma página, transporte simulado, bloqueio de requisições reais e destinos temporários. SQLite e CSV são exercitados em disco. Os testes unitários isolam as etapas.

| Cenário | Resultado a verificar |
| --- | --- |
| Carga inicial e conflito entre páginas | Igualdade entre URLs válidas esperadas e armazenadas, incluindo a última página. Comparação dos cinco campos, com título completo e precedência do detalhe |
| Reprocessamento | Duplicatas consolidadas, mudança válida refletida, livros ausentes ou rejeitados preservados |
| Catálogo vazio ou itens todos rejeitados | Vazio explícito segue a regra de retenção. Listagem com todos os livros rejeitados indica falha e preserva as saídas |
| Conexão e paginação | Recuperação até a terceira tentativa, falha de listagem preservando saídas, falha de detalhe rejeitando o item. Conferir os eventos registrados e os contadores de tentativas malsucedidas, falhas recuperadas, erros definitivos e total de erros segundo o contrato da CLI. Ciclo, destino externo e paginação interrompida recebem o diagnóstico apropriado |
| Armazenamento e CSV | Reversão durante a gravação da base. Quando a exportação falha após gravar a base, o SQLite novo e o CSV anterior permanecem disponíveis |
| Contratos e concorrência | CSV contém as mesmas URLs e valores da base, consideradas a conversão monetária e a proteção dos títulos. Resumos e logs conferem e apenas uma execução por destino tem acesso à publicação |

## Coleta obrigatória para aprovar a primeira versão

Use um diretório de validação vazio e uma conexão com a internet. Prepare um inventário independente a partir das páginas públicas, sem reutilizar o extrator do pipeline. Navegue da primeira à última página e registre as URLs das páginas percorridas. Para cada ocorrência de livro, registre a URL de detalhe na forma canônica, a página de origem e os quatro valores esperados conforme o [modelo de dados](data-model.md). Use o título completo, o preço em libras, a situação de estoque e as estrelas do detalhe. Para montar o conjunto esperado, use a primeira ocorrência válida de cada URL, conservando as demais ocorrências no inventário para conferir os contadores. Registre o momento da verificação e refaça a comparação se a fonte mudar entre o inventário e a coleta.

```sh
python -m pipeline_livros --help
python -m pipeline_livros --diretorio-saida saida/validacao-publica
python -m sqlite3 saida/validacao-publica/livros.sqlite3 \
  'SELECT url, titulo, preco_pence, disponibilidade, avaliacao FROM livros ORDER BY url'
```

O comando de coleta deve retornar 0, publicar os dois arquivos e indicar cobertura completa. Compare as URLs de listagem processadas e registradas no log com as do inventário, na mesma ordem. Confira os totais de páginas e ocorrências no resumo. Compare o conjunto de URLs de livros válidos esperadas com o SQLite e o CSV, verificando URLs faltantes, adicionais e duplicadas nas duas saídas, inclusive para a última página. Para cada URL, compare os cinco campos entre as três fontes. Compare o preço por valor, convertendo as libras do inventário e do CSV em pence exatos para conferir o inteiro armazenado. Verifique o título no CSV contra o valor esperado calculado a partir do título SQLite conforme a regra de proteção do [contrato do CSV](contracts/csv.md). Use um leitor de CSV que preserve campos entre aspas. Registre as divergências por URL e campo. A validação exige zero divergências e zero duplicatas nas saídas.

## Verificação do CSV no Calc

O teste de integração previsto abaixo usa um SQLite temporário com livros sintéticos válidos, cada um com URL distinta. Inclua títulos inofensivos como `=1+1`, `+1+1`, `-1+1`, `@teste`, equivalentes de largura completa e um título comum com acentos, vírgula e aspas. Exercite o exportador de produção sobre essa base e preserve o CSV gerado para a verificação manual.

```sh
python -m pytest -q -s tests/integration/test_csv_seguranca.py::test_exportacao_csv_para_calc
```

O teste deve informar o caminho do CSV no diretório temporário. Antes de abrir o arquivo em uma planilha, o teste lê o CSV com o módulo `csv` e verifica um apóstrofo ASCII antes de cada título de risco, a preservação do título comum, uma célula de título por linha lógica e a correspondência dos quatro demais campos com a base. A consulta ao SQLite deve retornar os títulos padronizados sem o prefixo acrescentado na exportação.

Em uma sessão local do LibreOffice Calc, abra apenas o CSV sintético gerado pelo teste para esta verificação, com as opções do [contrato do CSV](contracts/csv.md). Confirme que os títulos aparecem como texto em uma célula e que `=1+1` permanece visível como texto, sem o resultado numérico `2`. Registre a versão do Calc, as opções de importação e os resultados do teste automatizado e da abertura manual. A leitura automatizada demonstra a transformação do exportador. A abertura manual demonstra o comportamento no leitor documentado.

A aprovação da primeira versão exige a suíte local verde e a coleta pública bem-sucedida. O resultado da verificação no Calc comprova o comportamento do leitor documentado para o critério de proteção da exportação.
