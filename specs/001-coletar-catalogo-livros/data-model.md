# Modelo de dados — Pipeline de livros

## Página e detalhe brutos

A listagem fornece URL atual, próxima URL quando houver, indicação de página e itens em ordem. Cada detalhe fornece URL canônica e campos brutos de título, preço, disponibilidade e avaliação. Essas estruturas vivem em memória e podem ser testadas diretamente. A ausência explícita de livros é um resultado distinto de erro de leitura.

## Livro tratado

Uma linha da tabela `livros` representa um livro distinto. Todos os campos são obrigatórios.

| Campo SQLite | Tipo | Regra |
| --- | --- | --- |
| `url` | TEXT | Chave primária explícita, obrigatória. URL absoluta HTTPS do detalhe no host `books.toscrape.com`, sem consulta nem fragmento |
| `titulo` | TEXT | Título completo do detalhe com espaços nas extremidades removidos e conteúdo preservado |
| `preco_pence` | INTEGER | Preço em libras convertido para pence inteiros sem arredondar valores inválidos, entre zero e o máximo do inteiro SQLite |
| `disponibilidade` | TEXT | `em estoque` ou `sem estoque` |
| `avaliacao` | INTEGER | Uma a cinco estrelas. Os marcadores do site de `One` a `Five` são convertidos em inteiros |

A transformação aceita o preço em GBP com duas casas decimais. `In stock` sem quantidade ou com quantidade positiva representa estoque. `Out of stock` ou uma indicação explícita de zero unidades representa falta de estoque. Uma marcação contraditória, como `In stock` com zero unidades, ou um texto desconhecido causa rejeição. A disponibilidade não registra quantidade.

Para a identidade, resolver links relativos contra a URL da listagem, validar host, esquema, porta e rota, normalizar a porta HTTPS padrão e remover consulta e fragmento. Preservar o caminho do detalhe. URL inválida não é requisitada. A análise da página confirma que o link leva a um detalhe. SQLite aplica `NOT NULL` em todos os campos e restrições de domínio para preço, estoque, avaliação e título com conteúdo. A transformação valida também moeda, caminho e significado dos valores.

## Transições dos livros

| Estado anterior | Ocorrência na coleta | Resultado ao confirmar o lote |
| --- | --- | --- |
| Ausente | Primeiro detalhe válido da URL | Inserido |
| Existente | Primeiro detalhe válido com campos diferentes | Atualizado |
| Existente | Primeiro detalhe válido com campos iguais | Mantido sem mudança |
| Existente | Ausente da fonte ou sem ocorrência válida | Preservado e fora da contagem de mantidos sem mudança da coleta atual |
| Qualquer | Ocorrência válida posterior da mesma URL | Duplicata na coleta. A primeira ocorrência válida governa o lote |
| Qualquer | Ocorrência inválida | Rejeição. Uma ocorrência válida posterior ainda pode preencher o lote |

As classificações de gravação tornam-se públicas após o commit e, na primeira carga, após publicar a base. Não há exclusão de linhas por ausência na fonte.

## Execução e exportação

O resultado de execução mantém o estado geral, o estado de cada saída, as contagens e a etapa de falha quando aplicável. Os diagnósticos seguem para o log e o resumo para a saída padrão. O resumo está definido no [contrato da CLI](contracts/cli.md).

Cada exportação concluída representa todas as linhas confirmadas na base naquele momento, inclusive livros retidos de coletas anteriores. O CSV tem cinco colunas e ordenação por URL, descritas no [contrato CSV](contracts/csv.md).
