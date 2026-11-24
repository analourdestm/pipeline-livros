# Contrato da linha de comando

## Entrada

A partir da raiz do projeto, a interface prevista é `python -m pipeline_livros [--diretorio-saida DIRETORIO]`. O padrão é `saida/`, relativo ao diretório corrente. `--help` descreve as opções em português. A fonte da versão inicial é a listagem geral em `https://books.toscrape.com/`.

Uma execução usa `livros.sqlite3` e `livros.csv` no diretório de saída. O arquivo interno `.pipeline.lock` coordena o acesso concorrente ao diretório. O comando só grava os dados depois de avaliar a cobertura e a qualidade. A conexão à fonte é necessária para a coleta real.

## Saída e códigos de retorno

O comando escreve o resumo em português na saída padrão e envia diagnósticos à saída de erro por meio de `logging`. O resumo é destinado à leitura humana. A posição e a formatação das linhas podem evoluir.

| Código | Resultado |
| --- | --- |
| 0 | Sucesso, com SQLite e CSV publicados ou confirmados e sem rejeições de livros |
| 1 | Conclusão com erros de itens, com pelo menos uma rejeição e ambas as saídas confirmadas |
| 2 | Erro de sintaxe ou de argumentos |
| 3 | Falha de preparação, cobertura, qualidade dos dados, armazenamento ou exportação |

`--help` imprime ajuda e retorna 0 sem iniciar uma execução. Cada execução iniciada produz um resumo, inclusive em falhas de preparação. Uma falha de conexão recuperada gera diagnóstico, permite processar a página e não muda o código de saída por si só.

## Campos do resumo

- Estado da execução e etapa de falha, quando houver.
- Estado do SQLite e do CSV, com os caminhos correspondentes.
- Páginas da listagem processadas, ocorrências de livros detectadas, itens rejeitados e duplicatas válidas na mesma coleta.
- Livros inseridos, atualizados e mantidos sem mudança entre os livros válidos tratados no lote.
- Linhas de dados publicadas no CSV, fora o cabeçalho.
- Total de erros registrados, com subtotais de tentativas de conexão malsucedidas e erros definitivos. Informar também quantas tentativas malsucedidas foram recuperadas, como subconjunto do primeiro subtotal.

Uma página conta quando sua listagem for interpretada com sucesso. Cada ocorrência encontrada na listagem entra na contagem de detectadas. Uma ocorrência inválida conta como rejeição. Ocorrências válidas posteriores de uma mesma URL contam como duplicatas. O primeiro livro válido da URL entra na classificação de escrita. Uma URL retida sem ocorrência válida fica fora dessa classificação.

Os números de escrita se tornam efetivos após a confirmação da base. Os números do CSV se tornam efetivos após a publicação do arquivo. Uma etapa de escrita que falhou ou deixou de ser executada reporta zero mudanças publicadas. Na exportação bem-sucedida de uma base vazia, zero linhas com estado de CSV atualizado representa um arquivo válido com cabeçalho.

Os logs incluem etapa, causa e, quando disponível, página, livro ou destino. Cada página da listagem interpretada com sucesso registra um evento informativo com a URL normalizada da página para conferência de cobertura. Cada tentativa malsucedida conta como um evento de erro e recebe diagnóstico com seu número. Se a página for lida em seguida, as tentativas anteriores daquela página contam também no subconjunto de falhas recuperadas. Um item rejeitado ou uma etapa que precisa encerrar gera um evento definitivo com seu desfecho. O total soma as tentativas malsucedidas e os erros definitivos registrados. Eventos informativos e o subtotal de falhas recuperadas ficam fora dessa soma.

Exemplos com os demais passos sem erros. Uma falha seguida de recuperação gera total 1, uma tentativa malsucedida, uma falha recuperada e zero erros definitivos. Três falhas que esgotam as tentativas de uma página geram total 4, três tentativas malsucedidas, zero recuperadas e um erro definitivo pelo desfecho. O estado geral e o código de saída seguem o resultado da execução definido acima.

## Estado das saídas

| Situação | SQLite | CSV |
| --- | --- | --- |
| Sucesso ou conclusão com erros de itens | Atualizado | Atualizado |
| Falha antes de concluir a gravação | Preservado ou ausente | Preservado ou ausente |
| Falha na exportação após confirmação da base | Atualizado | Desatualizado se existir, ausente em caso contrário |

`Atualizado` indica que a etapa concluiu na execução corrente. `Preservado` indica que a saída anterior continua disponível e não foi publicada nesta execução. `Desatualizado` indica que o CSV presente não foi publicado para refletir a base confirmada nesta execução.
