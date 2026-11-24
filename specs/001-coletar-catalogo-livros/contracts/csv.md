# Contrato do CSV

O arquivo `livros.csv` usa UTF-8, vírgula como separador, aspas duplas para delimitação e CRLF como terminador de registro. Aspas internas são duplicadas conforme as regras do módulo `csv`. Há um cabeçalho obrigatório e uma linha lógica por livro da base confirmada, em ordem crescente de URL.

| Posição | Coluna | Representação |
| --- | --- | --- |
| 1 | `titulo` | Texto do título padronizado, com proteção de fórmula quando aplicável |
| 2 | `preco_gbp` | Preço em libras com ponto decimal e duas casas, sem símbolo de moeda |
| 3 | `disponibilidade` | `em estoque` ou `sem estoque` |
| 4 | `avaliacao` | Inteiro de 1 a 5 |
| 5 | `url` | URL canônica do livro |

## Títulos em planilhas

Na exportação, títulos padronizados cujo primeiro caractere possa iniciar fórmula recebem um apóstrofo ASCII antes da serialização. A regra cobre `=`, `+`, `-`, `@`, os equivalentes de largura completa e caracteres iniciais de controle relevantes, como tabulação, CR e LF, se ainda presentes após a padronização. As aspas do CSV continuam a delimitar títulos com vírgulas, aspas ou quebras de linha. O título padronizado permanece no SQLite. Dependendo da importação, o apóstrofo pode fazer parte do texto exibido ou lido.

O leitor de referência é o LibreOffice Calc no macOS. Abrir como Texto CSV, com UTF-8, vírgula e aspas duplas. Definir a coluna `titulo` como **Texto** e desativar **Avaliar fórmulas**. Para visualizar `preco_gbp` como número com ponto decimal, selecionar a localidade Inglês (EUA) para a importação ou para a coluna. O procedimento verifica o arquivo gerado pelo pipeline. A base é a referência para consumidores que precisem do título padronizado sem o prefixo de exportação.

## Publicação

O arquivo é escrito em um temporário vizinho ao destino. A substituição ocorre após gravar, descarregar os buffers e fechar o temporário. Uma falha de exportação preserva o CSV anterior, quando houver. O estado correspondente aparece no [contrato da CLI](cli.md).
