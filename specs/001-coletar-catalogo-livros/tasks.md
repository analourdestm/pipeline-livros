---
description: "Tarefas de implementação do pipeline local de livros"
---

# Tasks: Coletar o catálogo de livros

**Referências** — [Constituição v1.0.0](../../.specify/memory/constitution.md), [especificação e decisões de Clarify](spec.md), [plano](plan.md), [pesquisa](research.md), [modelo de dados](data-model.md), [contrato da CLI](contracts/cli.md), [contrato do CSV](contracts/csv.md) e [guia de validação](quickstart.md).

**Formato** — Os caminhos nas tarefas são relativos à raiz do repositório. `[P]` indica que a tarefa pode rodar em paralelo com as companheiras indicadas, após concluir as dependências e respeitar os arquivos de cada tarefa. `[US1]` a `[US4]` correspondem às histórias da especificação. Em cada história, escrever primeiro os testes que demonstram a lacuna e executá-los novamente após a implementação.

## Fase 1 — Preparação do projeto

**Objetivo.** Preparar o pacote local e o ambiente Python no macOS.

- [ ] T001 [P] Criar `pyproject.toml` e `pipeline_livros/__init__.py` para CPython 3.14.x. Declarar Requests e Beautiful Soup como dependências de execução e Pytest no extra `dev`, com instalação pelo `pip` em `.venv`.
- [ ] T002 [P] Criar `.gitignore` na raiz para ignorar `.venv`, caches de Python e Pytest, metadados de instalação e `saida/`, incluindo as bases, os CSVs, os temporários e o arquivo de bloqueio do destino padrão.

**Conclusão.** A instalação `python -m pip install '.[dev]'` funciona em uma `.venv` no macOS, o pacote pode ser importado e os arquivos gerados no destino padrão são ignorados.

## Fase 2 — Base compartilhada

**Objetivo.** Preparar dados de referência, transporte simulado e exclusão mútua no diretório de saída.

- [ ] T003 [P] Criar `tests/fixtures/catalogo/index.html`, `tests/fixtures/catalogo/page-2.html`, `tests/fixtures/catalogo/livro-a.html`, `tests/fixtures/catalogo/livro-b.html` e `tests/fixtures/catalogo/esperado.json` com catálogo sintético multipágina, um livro exclusivo da última página e inventário esperado de páginas, URLs e campos para comparação independente. Depende da Fase 1.
- [ ] T004 [P] Criar `tests/conftest.py` com transporte HTTP simulado por URL, respostas e exceções programáveis e espera de repetição simulada. Bloquear chamadas reais do Requests na suíte e usar `tmp_path` para os destinos de teste. Depende da Fase 1.
- [ ] T005 [P] Criar `tests/unit/test_bloqueio.py` para comprovar que duas invocações que disputam o mesmo diretório não publicam simultaneamente, que destinos distintos são independentes e que o bloqueio é liberado ao fechar o descritor. Depende da Fase 1.
- [ ] T006 Implementar em `pipeline_livros/pipeline.py` a preparação do destino e o bloqueio não bloqueante por diretório com `fcntl.flock` sobre `.pipeline.lock`. Definir o escopo de aquisição desde a preparação da execução até terminar as publicações e liberar o descritor mesmo em falhas. Depende de T005.

**Conclusão.** Os testes demonstram o bloqueio por diretório. O inventário sintético, o transporte simulado e os destinos temporários permitem testar as histórias sem internet.

## Fase 3 — US1 · Carregar o catálogo localmente (P1)

**Objetivo.** Percorrer a listagem geral e consultar os livros tratados no SQLite.

**Teste independente.** Rodar a carga contra o catálogo multipágina simulado com SQLite inicialmente ausente e comparar o inventário esperado com as páginas percorridas e os cinco campos de cada URL válida no banco.

### Testes

- [ ] T007 [P] [US1] Criar `tests/unit/test_extracao.py` para verificar resolução de links, destino HTTPS permitido, recusa de redirecionamentos e rotas incorretas, páginas anterior e final da sequência, catálogo explicitamente vazio, ciclo, interrupção prematura, HTML inválido, cartão sem link, encoding de acentos e libras e leitura dos campos do detalhe. Cobrir também timeout, recuperação e limite de três tentativas por página. Depende da Fase 2.
- [ ] T008 [P] [US1] Criar `tests/unit/test_transformacao.py` para testar normalização dos cinco campos, valores ausentes e inválidos, precedência do detalhe, equivalência de URLs e disponibilidade explícita sem estoque. Depende da Fase 2.
- [ ] T009 [P] [US1] Criar `tests/unit/test_armazenamento.py` para verificar criação da tabela, restrições, carga inicial, consulta ordenada e ausência de publicação incompleta quando a primeira gravação falhar, usando SQLite real em destino temporário. Depende da Fase 2.
- [ ] T010 [P] [US1] Criar `tests/integration/test_carga.py` para testar a entrada local da CLI com transporte simulado. Comparar as páginas e os cinco campos por URL com `tests/fixtures/catalogo/esperado.json`. Cobrir a última página, um item inválido com diagnóstico, título completo, valores divergentes entre listagem e detalhe, links relativo e absoluto equivalentes e catálogo explicitamente vazio. Depende da Fase 2.

### Implementação

- [ ] T011 [US1] Implementar o livro tratado e a validação em `pipeline_livros/transformacao.py`, aplicando as definições de [Livro.url, Livro.titulo, Livro.preco_pence, Livro.disponibilidade e Livro.avaliacao em data-model.md](data-model.md#livro-tratado). Expor a normalização de URL usada pela extração antes do GET e retornar motivo de rejeição para dados inválidos. Depende de T007–T010.
- [ ] T012 [P] [US1] Implementar em `pipeline_livros/extracao.py` a sessão Requests, a validação HTTPS de links e a política de timeout e tentativas da [pesquisa](research.md#transporte-paginação-e-html). Analisar HTML com Beautiful Soup e `html.parser` para extrair listagem, próximo link, evidências de paginação e campos brutos do detalhe. Classificar leitura de listagem, leitura de detalhe e tentativa de conexão para o fluxo de execução. Depende de T011.
- [ ] T013 [P] [US1] Implementar em `pipeline_livros/armazenamento.py` a tabela `livros` e a carga inicial com SQL parametrizado e transação única. Aplicar [Livro.url, Livro.titulo, Livro.preco_pence, Livro.disponibilidade e Livro.avaliacao em data-model.md](data-model.md#livro-tratado). Confirmar e fechar a base inicial temporária antes da publicação atômica e expor consulta ordenada por URL. Depende de T011.
- [ ] T014 [US1] Integrar a carga inicial em `pipeline_livros/pipeline.py`. Percorrer as páginas em ordem, verificar ciclos, progressão e contagem anunciada quando disponíveis, rejeitar itens inválidos com causa, reter a primeira ocorrência válida por URL e gravar apenas após cobertura e qualidade confirmadas. Distinguir vazio explícito de listagem irreconhecível e de rejeição de todos os itens. Depende de T006, T012 e T013.
- [ ] T015 [US1] Conectar a carga inicial em `pipeline_livros/__main__.py` com `argparse`, ajuda em português, `--diretorio-saida`, configuração de `logging` e chamada ao fluxo de carga. Depende de T014.
- [ ] T016 [P] [US1] Criar `README.md` com configuração gratuita no macOS, ambiente virtual, comando de carga, ajuda da CLI e consulta SQLite. Basear o guia nos contratos aprovados e em `specs/001-coletar-catalogo-livros/quickstart.md`. Depende de T011.

**Conclusão.** T007–T010 passam sem rede. O catálogo de referência produz uma base consultável com todos os livros válidos, uma linha por URL e diagnóstico para cada item rejeitado. A pessoa operadora consegue seguir em português o procedimento de carga local.

## Fase 4 — US2 · Atualizar os livros sem duplicar registros (P1)

**Objetivo.** Reprocessar a fonte preservando a identidade por URL e os últimos dados válidos.

**Teste independente.** Rodar a coleta sobre uma base de referência já populada com itens repetidos, alterados, ausentes e novos. Conferir linhas e contagens por URL antes e depois.

### Testes

- [ ] T017 [P] [US2] Criar `tests/unit/test_atualizacao_sqlite.py` para verificar classificação de inserido, atualizado e mantido sem mudança, preço alterado sem duplicação, título igual com URL diferente, preservação de livros ausentes ou rejeitados e reversão de um lote interrompido. Depende da conclusão da US1.
- [ ] T018 [P] [US2] Criar `tests/integration/test_reprocessamento.py` para repetir a carga sobre a mesma base, exercitar duplicatas válidas em páginas diferentes, primeiras ocorrências inválidas seguidas de válidas e a precedência da primeira ocorrência válida quando há divergência entre duplicatas. Conferir que as contagens confirmadas representam somente o lote atual. Depende da conclusão da US1.

### Implementação

- [ ] T019 [US2] Implementar em `pipeline_livros/armazenamento.py` a atualização transacional da base existente, usando [Livro.url e as transições de Livro em data-model.md](data-model.md#transições-dos-livros). Comparar campos antes de gravar, preservar linhas ausentes ou rejeitadas e devolver contagens somente após a confirmação. Depende de T017 e T018.
- [ ] T020 [US2] Integrar as classificações de carga em `pipeline_livros/pipeline.py` e contabilizar duplicatas válidas posteriores à primeira ocorrência válida usando a mesma tabela de identidades da US1. Ao reverter a gravação, manter a base anterior e zero mudanças publicadas. Depende de T019.

**Conclusão.** T017 e T018 passam. Duas coletas idênticas preservam a contagem e a unicidade da base. Uma alteração válida modifica apenas a linha da URL correspondente, e registros ausentes ou rejeitados mantêm os valores anteriores.

## Fase 5 — US3 · Exportar a base tratada (P2)

**Objetivo.** Publicar um CSV íntegro a partir do conjunto confirmado no SQLite e proteger títulos que possam ser interpretados como fórmulas.

**Teste independente.** Exportar uma base de referência já populada. Comparar o cabeçalho e todos os campos por URL, abrir o arquivo sintético no Calc conforme o contrato e conferir uma única célula de título por livro, com fórmulas exibidas como texto.

### Testes

- [ ] T021 [P] [US3] Criar `tests/unit/test_exportacao.py` para verificar o [contrato do CSV](contracts/csv.md) com base de referência, incluindo cabeçalho, ordenação, UTF-8, pence em libras, acentos, vírgulas, aspas, zero linhas para base vazia, substituição do CSV anterior e preservação do arquivo em falhas de preparação ou publicação. Depende da Fase 2.
- [ ] T022 [P] [US3] Criar `tests/integration/test_csv_seguranca.py` com `test_exportacao_csv_para_calc`. Preparar SQLite temporário com títulos sintéticos inofensivos do guia, chamar o exportador real, verificar a transformação seletiva e os cinco campos com o leitor `csv`, conferir o título no SQLite e imprimir o caminho do CSV para a verificação manual. Depende da Fase 2.

### Implementação

- [ ] T023 [P] [US3] Implementar em `pipeline_livros/exportacao.py` o [contrato do CSV](contracts/csv.md), publicando as linhas confirmadas por ordem de URL, convertendo o preço com precisão decimal e protegendo apenas títulos de risco na representação exportada. Escrever o arquivo temporário no diretório de destino, fechá-lo, publicar com `os.replace` e limpar o temporário em falhas tratadas. Depende de T021 e T022.
- [ ] T024 [US3] Integrar o exportador em `pipeline_livros/pipeline.py` após a confirmação da base. Usar todas as linhas confirmadas, inclusive as retidas, contabilizar apenas linhas publicadas e propagar o estado do SQLite e do CSV. Estender `tests/integration/test_reprocessamento.py` para conferir a substituição com um único cabeçalho e uma linha por livro armazenado. Verificar também a exportação de livros retidos para um catálogo explicitamente vazio e o arquivo só com cabeçalho em uma primeira carga vazia. Depende de T020 e T023.

**Conclusão.** T021, T022 e o teste de reprocessamento passam. Uma exportação concluída publica todos os registros, com proteção seletiva no arquivo e títulos padronizados preservados no SQLite. A verificação manual da história é concluída na Fase 7.

## Fase 6 — US4 · Conferir o resultado da execução (P2)

**Objetivo.** Mostrar o resultado de cada etapa, distinguir falhas temporárias de erros definitivos e preservar as saídas conforme a etapa da falha.

**Teste independente.** Usar o catálogo simulado e destinos temporários para reproduzir sucesso, rejeições, falhas de listagem, detalhe, qualidade, armazenamento e exportação. Comparar estado dos arquivos, logs, resumo e código de saída.

### Testes

- [ ] T025 [P] [US4] Criar `tests/integration/test_contrato_cli.py` para verificar ajuda, argumentos inválidos, códigos de saída 0 a 3, resumo na saída padrão e diagnósticos na saída de erro. Conferir contagens em sucesso e conclusão com erros, total de eventos na recuperação e no esgotamento das tentativas, e a ordem das URLs da listagem registradas no log. Depende da Fase 2.
- [ ] T026 [P] [US4] Criar `tests/integration/test_falhas_execucao.py` para simular falhas recuperadas na listagem e no detalhe, três tentativas esgotadas em ambos, rejeição isolada, todos os itens rejeitados com e sem arquivos anteriores, ciclo ou paginação interrompida, falhas de SQLite e CSV e disputa pelo mesmo destino. Conferir os dados preservados, a ausência de publicação quando prevista e as contagens confirmadas. Depende da Fase 2.

### Implementação

- [ ] T027 [US4] Implementar em `pipeline_livros/pipeline.py` os estados e contadores de execução do [contrato da CLI](contracts/cli.md). Registrar URLs de listagem processadas em ordem, cada tentativa malsucedida, as recuperações como subconjunto e os desfechos definitivos com etapa, causa e contexto. Aplicar as regras de preservação de FR-010 e manter zero contagens de escrita em etapas que não confirmaram a publicação. Depende de T024–T026.
- [ ] T028 [US4] Implementar em `pipeline_livros/__main__.py` a apresentação dos estados das saídas, resumo completo em português e códigos de saída do [contrato da CLI](contracts/cli.md), com `logging` na saída de erro e resumo na saída padrão. Depende de T027.

**Conclusão.** T025 e T026 passam. Cada desfecho produz o resumo contratado, com diagnóstico de falhas e estado correto dos arquivos. Os totais de erros incluem tentativas malsucedidas e desfechos definitivos, sem contar recuperações duas vezes.

## Fase 7 — Documentação e validação de entrega

**Objetivo.** Verificar a primeira versão no macOS com a suíte offline, a fonte pública e o leitor de planilhas documentado.

- [ ] T029 [P] Completar `README.md` com as versões validadas e a finalidade das dependências, os comandos da CLI e da suíte offline, a interpretação do resumo e dos códigos de saída, os arquivos produzidos e a abertura segura no LibreOffice Calc conforme `specs/001-coletar-catalogo-livros/contracts/csv.md`. Depende de T028.
- [ ] T030 [P] Executar a suíte completa em `tests/unit/` e `tests/integration/` com `python -m pytest`, sem internet. Verificar regras de dados, bloqueio de rede, arquivos, diagnósticos e falhas conforme `specs/001-coletar-catalogo-livros/quickstart.md`. Depende de T028.
- [ ] T031 [P] Executar a coleta pública no macOS em `saida/validacao-publica/livros.sqlite3` e `saida/validacao-publica/livros.csv` com o procedimento de `specs/001-coletar-catalogo-livros/quickstart.md`. Conferir código 0, páginas por URL e em ordem, livros por URL e os cinco campos entre inventário independente, SQLite e CSV, com a conversão de preço e a proteção de títulos previstas. Guardar a evidência de validação localmente no diretório de saída. Depende de T029 e T030.
- [ ] T032 [P] Gerar o CSV sintético pelo teste em `tests/integration/test_csv_seguranca.py` e executar a verificação controlada no LibreOffice Calc de `specs/001-coletar-catalogo-livros/quickstart.md`. Conferir a proteção no arquivo, a base intacta e a célula de teste como texto sem avaliação de fórmula. Registrar localmente em `saida/validacao-calc/` a versão do leitor, as opções e o resultado. Depende de T029 e T030.
- [ ] T033 Revisar a conformidade final de `pipeline_livros/`, `tests/` e `README.md` com os princípios da constituição e a matriz abaixo. Conferir os resultados da suíte offline, da coleta pública e do Calc antes de aprovar a primeira versão. Depende de T031 e T032.

**Conclusão.** Suíte local verde sem rede, coleta pública completa com zero divergências nas saídas, proteção do CSV confirmada no Calc, documentação em português conferida e revisão da constituição concluída.

## Dependências e execução em paralelo

**Ordem para implementação individual.** Fases 1 → 2 → US1 → US2 → US3 → US4 → 7. Dentro de uma fase, seguir a ordem dos IDs e as dependências. US1 e US2 têm prioridade P1. US3 e US4 têm prioridade P2.

| Fase ou história | Paralelismo após as dependências | Integração |
| --- | --- | --- |
| Preparação | T001 e T002 | Instalação e verificação do ambiente |
| Base compartilhada | T003, T004 e T005 | T006 implementa o bloqueio após o teste |
| US1 | T007–T010. Depois de T011, T012, T013 e T016 podem rodar juntas | T014 e T015 integram módulos e entrada CLI |
| US2 | T017 e T018 | T019 atualiza a base e T020 liga as contagens ao fluxo |
| US3 | T021 e T022 podem ser escritos após a base compartilhada. T023 pode avançar enquanto a US2 trabalha em armazenamento | T024 aguarda T020 e T023 para ligar a exportação ao fluxo |
| US4 | T025 e T026 podem ser escritos após a base compartilhada | T027 aguarda T024–T026. T028 fecha a apresentação |
| Validação | T029 e T030. Depois, T031 e T032 usam destinos distintos | T033 consolida a revisão |

As tarefas que alteram `pipeline_livros/pipeline.py` seguem T006 → T014 → T020 → T024 → T027. As que modificam `pipeline_livros/__main__.py` seguem T015 → T028. Os testes de contrato das histórias posteriores podem ser preparados antes da integração. Rode os testes da história quando as interfaces necessárias estiverem disponíveis.

## Matriz de cobertura

| Requisitos funcionais | Implementação | Verificação |
| --- | --- | --- |
| FR-001 — Paginação completa | T012, T014 | T007, T010, T026, T031 |
| FR-002 — Cinco campos e precedência do detalhe | T011, T012 | T008, T010, T031 |
| FR-003 — Validação e normalização | T011, T013 | T008–T010, T022 |
| FR-004 — SQLite local | T013, T014, T019 | T009, T010, T017, T026 |
| FR-005 — Exportação e proteção | T023, T024 | T021, T022, T024, T031, T032 |
| FR-006 — Unicidade, atualização e retenção | T011, T013, T014, T019, T020 | T010, T017, T018, T031 |
| FR-007 — Tentativas e erros | T012, T014, T027, T028 | T007, T010, T025, T026 |
| FR-008 — Resumo e contagens | T020, T024, T027, T028 | T018, T025, T026 |
| FR-009 — Execução gratuita e instruções em português | T001, T015, T016, T029 | T010, T025, T031, T032 |
| FR-010 — Preservação das saídas | T013, T014, T019, T023, T024, T027 | T009, T017, T021, T026 |

| Critérios de aceite da especificação | Tarefas de verificação |
| --- | --- |
| US1.1 — Todas as páginas e última página | T007, T010, T031 |
| US1.2 — Título completo e cinco valores tratados | T008, T010 |
| US1.3 — Carga parcial com rejeição e diagnóstico | T010, T026 |
| US1.4 — Carga local gratuita com guia em português | T016, T029, T031 |
| US1.5 — Links equivalentes produzem uma linha | T008, T010 |
| US1.6 — Valores divergentes seguem o detalhe | T008, T010 |
| US2.1 — Repetição da carga e duplicatas entre páginas | T017, T018 |
| US2.2 — Atualizar preço e inserir outra URL com título igual | T017, T018 |
| US3.1 — Cabeçalho e equivalência dos campos por URL | T021, T022, T031 |
| US3.2 — Acentos, vírgulas e aspas em uma célula | T021, T022, T032 |
| US3.3 — Substituição do CSV anterior | T021, T024 |
| US3.4 — Título protegido no Calc e preservado na base | T022, T032 |
| US4.1 — Resumo de sucesso e contagens | T025, T031 |
| US4.2 — Uma rejeição registrada, saídas atualizadas | T025, T026 |
| US4.3 — Listagem indisponível após três tentativas | T007, T026 |
| US4.4 — CSV falha após atualizar a base | T021, T026 |
| US4.5 — Gravação SQLite falha e ambas as saídas são preservadas | T017, T026 |
| US4.6 — Conexão recuperada na segunda ou terceira tentativa | T007, T025, T026 |
| US4.7 — Detalhe indisponível após três tentativas | T007, T026 |
| US4.8 — Todos os livros rejeitados, com e sem saídas anteriores | T026 |

| Critérios de sucesso | Evidência prevista |
| --- | --- |
| SC-001 — Cobertura e livros válidos | T010, T031 |
| SC-002 — Campos corretos e rejeição de dados inválidos | T008, T010, T031 |
| SC-003 — Reprocessamento sem duplicatas | T017, T018 |
| SC-004 — Correspondência do CSV e proteção no leitor | T021, T022, T024, T031, T032 |
| SC-005 — Estados, diagnósticos e preservação em falhas | T007, T025, T026 |
| SC-006 — Execução local guiada em português | T029, T031, T032 |
| SC-007 — Suíte offline e coleta pública obrigatórias | T030, T031, T033 |

## Estratégia de implementação e MVP

O **MVP de demonstração** é a carga local da US1 após as Fases 1 a 3. Uma invocação percorre o catálogo de referência, valida os livros, rejeita dados inválidos com diagnóstico e permite consultar no SQLite todos os registros válidos, inclusive os da última página. Validar esse incremento antes de seguir.

A **primeira versão aprovada** inclui as quatro histórias. A US2 acrescenta atualização recorrente, a US3 publica o CSV tratado com proteção para o Calc e a US4 completa o resumo e as garantias em falhas. A Fase 7 comprova a entrega com testes sem internet, uma coleta bem-sucedida na fonte pública e a verificação controlada do CSV.

Manter os módulos Python do [plano aprovado](plan.md), o processamento em série e testes com entradas pequenas. Usar funções e nomes diretos e a biblioteca padrão onde previsto no plano.
