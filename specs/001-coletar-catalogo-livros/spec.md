# Feature Specification: Coletar o catálogo de livros

**Feature Branch** — `main`

**Created** — 2026-11-24

**Status** — Rascunho validado

**Input** — Automatizar a coleta, o tratamento e o armazenamento local do catálogo público do [Books to Scrape](https://books.toscrape.com/), com exportação e acompanhamento de cada execução.

## Clarifications

### Session 2026-11-24

- Q: Como o pipeline deve reagir a uma falha temporária de conexão ao carregar uma página do catálogo ou o detalhe de um livro? → A: Fazer até três tentativas no total por página. Se a falha persistir na listagem, encerrar a coleta e preservar as saídas anteriores. Se persistir no detalhe, rejeitar apenas aquele livro.
- Q: Se a listagem contém livros, mas todos forem rejeitados, como o pipeline deve encerrar a execução? → A: Indicar falha de qualidade dos dados, preservar as saídas anteriores e, se for a primeira execução, encerrar sem criar a base ou o CSV.
- Q: Se a listagem e a página de detalhe mostrarem valores válidos, mas diferentes, para o preço, a disponibilidade ou a avaliação de um livro, qual valor deve ser armazenado? → A: Armazenar o valor da página de detalhe.
- Q: Como o pipeline deve tratar um título que pode ser interpretado como fórmula ao abrir o CSV em uma planilha? → A: Preservar o título na base e adaptar apenas sua representação no CSV para que seja lido como texto nos leitores de planilha documentados.
- Q: A aprovação da primeira versão deve exigir uma coleta bem-sucedida no site público, além dos testes locais com um catálogo de referência? → A: Exigir a aprovação dos testes locais, executáveis sem internet, e pelo menos uma coleta bem-sucedida no site público antes de aprovar a primeira versão do pipeline.

## User Scenarios & Testing

### História 1 — Carregar o catálogo localmente (P1)

Como pessoa operadora do pipeline, quero percorrer o catálogo inteiro em uma execução e consultar os livros tratados no SQLite para trabalhar com uma base local.

**Motivo da prioridade.** A carga local entrega o catálogo tratado para consulta.

**Teste independente.** Executar a carga com um catálogo de referência multipágina e uma base vazia, em ambiente local sem serviços pagos, e comparar os registros gravados com os itens válidos da fonte.

**Critérios de aceite**

1. **Dado** um catálogo acessível com mais de uma página, **quando** a pessoa operadora inicia a carga, **então** o pipeline percorre da primeira à última página automaticamente e grava um registro por URL de livro válida, incluindo os livros da última página. (FR-001, FR-002, FR-004, FR-006)
2. **Dados** um título abreviado na listagem, um preço em libras e uma avaliação em estrelas, **quando** o livro é processado, **então** a base contém o título completo, o preço decimal em libras, a disponibilidade padronizada, a avaliação inteira e a URL absoluta da página do livro. (FR-002, FR-003, FR-004)
3. **Dados** um livro válido e outro com campo obrigatório ausente ou inválido, **quando** a carga termina, **então** o livro válido está na base e o inválido é rejeitado com registro da causa. (FR-003, FR-004, FR-007)
4. **Dada** uma máquina local com acesso ao catálogo e permissão de gravação na pasta de trabalho, **quando** a pessoa segue o guia em português, **então** consegue concluir a carga sem pagar por ferramenta ou serviço. (FR-009)
5. **Dados** dois links para o mesmo livro, um relativo e outro absoluto com parâmetros e fragmento, **quando** ambos são processados, **então** a base contém uma única linha com a URL absoluta padronizada. (FR-003, FR-006)
6. **Dados** um preço, uma disponibilidade ou uma avaliação com valores válidos, mas diferentes, na listagem e na página de detalhe, **quando** o livro é processado, **então** o valor armazenado para cada campo divergente é o da página de detalhe. (FR-002, FR-004)

---

### História 2 — Atualizar os livros sem duplicar registros (P1)

Como pessoa operadora, quero executar novamente a coleta para atualizar os dados dos livros sem acumular cópias.

**Motivo da prioridade.** Em coletas recorrentes, a base precisa manter uma contagem confiável e refletir os valores válidos mais recentes.

**Teste independente.** Partir de uma base local com registros conhecidos e executar a coleta com itens repetidos, alterados e novos.

**Critérios de aceite**

1. **Dada** uma carga completa, **quando** o mesmo catálogo é coletado novamente, inclusive com um livro repetido em páginas diferentes, **então** a base continua com a mesma contagem e uma única linha por URL padronizada. (FR-006)
2. **Dados** um preço válido alterado para uma URL já registrada e um novo livro com outra URL cujo título coincide com o de um livro existente, **quando** a carga termina, **então** o preço é atualizado no registro existente e o novo livro recebe seu próprio registro. (FR-004, FR-006)

---

### História 3 — Exportar a base tratada (P2)

Como pessoa que analisa o catálogo, quero abrir os dados em um arquivo CSV para consultar ou compartilhar os resultados.

**Motivo da prioridade.** O CSV permite usar os dados tratados em ferramentas de análise.

**Teste independente.** Gerar o arquivo a partir de uma base local com registros conhecidos e comparar os valores exportados com os armazenados.

**Critérios de aceite**

1. **Dada** uma base tratada, **quando** a exportação é concluída, **então** o CSV tem cabeçalho com os cinco campos e uma linha por livro armazenado, com valores equivalentes aos da base, respeitando a representação protegida dos títulos quando aplicável. (FR-005)
2. **Dado** um título com acentos, vírgulas ou aspas, **quando** o CSV é aberto em um leitor compatível, **então** o título permanece íntegro em uma única célula e os outros campos mantêm suas posições. (FR-005)
3. **Dado** um CSV de uma execução anterior, **quando** uma nova exportação é concluída, **então** o arquivo reflete a base atual com um único cabeçalho e uma linha por livro. (FR-005, FR-006)
4. **Dado** um título válido que um leitor de planilha documentado interpretaria como fórmula, **quando** o CSV gerado é aberto nesse leitor conforme o guia, **então** o título é exibido como texto em uma única célula e a fórmula não é avaliada. A base mantém o título conforme a padronização de FR-003. (FR-003, FR-005, FR-009)

---

### História 4 — Conferir o resultado da execução (P2)

Como pessoa operadora, quero saber se a coleta terminou e onde ocorreram erros para decidir se posso usar os dados ou preciso executar o pipeline novamente.

**Motivo da prioridade.** A cobertura da coleta e o estado das saídas precisam estar visíveis para que a pessoa operadora possa avaliar os resultados.

**Teste independente.** Executar contra um catálogo de referência com um registro inválido e repetir simulando, em execuções separadas, falhas de conexão recuperáveis e persistentes na listagem e no detalhe, uma falha de armazenamento e uma falha de exportação. Conferir o número de tentativas, os registros de erro, o resumo e as saídas de cada execução.

**Critérios de aceite**

1. **Dada** uma coleta e exportação sem erros, **quando** a execução termina, **então** o resumo indica sucesso e apresenta as contagens de páginas, livros processados e linhas exportadas. (FR-008)
2. **Dado** um único livro inválido entre livros válidos, **quando** a execução termina com a base e o CSV atualizados, **então** o resumo indica conclusão com erros e contabiliza uma rejeição. O registro de erro informa a etapa, a causa disponível e o livro ou a página de origem. (FR-007, FR-008)
3. **Dadas** três falhas consecutivas de conexão ao carregar uma página necessária da listagem, **quando** a terceira tentativa falha, **então** o pipeline encerra a coleta, o resumo indica falha na coleta e as saídas da execução anterior são preservadas. (FR-001, FR-007, FR-008, FR-010)
4. **Dada** uma atualização da base concluída e uma falha ao gravar o novo CSV, **quando** a execução termina, **então** o resumo indica falha na exportação, informa que a base foi atualizada e sinaliza que o arquivo esperado está ausente ou desatualizado. Se já existia um CSV válido, ele continua íntegro. (FR-005, FR-007, FR-008, FR-010)
5. **Dadas** saídas de uma execução anterior e uma falha durante a gravação da base, **quando** a execução termina, **então** o resumo indica falha de armazenamento e as duas saídas anteriores continuam disponíveis com os mesmos dados. (FR-007, FR-008, FR-010)
6. **Dada** uma falha de conexão na primeira tentativa de ler uma página da listagem ou de detalhe, **quando** a leitura tem êxito na segunda ou terceira tentativa, **então** o pipeline continua a coleta e processa a página normalmente. (FR-001, FR-007)
7. **Dadas** três falhas consecutivas de conexão ao carregar o detalhe de um livro, **quando** a terceira tentativa falha, **então** o pipeline rejeita esse livro, registra a falha e continua com os demais. Se esse livro já estava na base, seus últimos valores válidos são preservados. (FR-004, FR-007, FR-008)
8. **Dada** uma listagem percorrida por completo com pelo menos um livro detectado, **quando** todos os livros são rejeitados, **então** o resumo indica falha de qualidade dos dados e informa o total de rejeições. O conteúdo da base e do CSV anteriores é preservado. Em uma primeira execução, nenhuma dessas saídas é criada. (FR-008, FR-010)

### Edge Cases

- Uma página que aponta para uma página já visitada cria um ciclo. O pipeline encerra a coleta com falha e identifica a página no registro de erro.
- Um campo de disponibilidade ausente ou irreconhecível torna o livro inválido. Uma indicação explícita de falta de estoque é um valor válido.
- Uma falha de leitura restrita ao detalhe de um livro rejeita esse item e permite processar os demais. Para falhas de conexão, a rejeição ocorre após três tentativas sem êxito. Um livro já armazenado cujo novo item foi rejeitado mantém seus últimos valores válidos.
- Uma falha na gravação da base preserva os dados anteriores e encerra a execução com indicação de falha de armazenamento. O CSV anterior é preservado.
- Uma listagem percorrida por completo que contém livros, todos rejeitados, caracteriza falha de qualidade dos dados. Aplica-se a regra de preservação de FR-010.
- Se a fonte indicar explicitamente um catálogo vazio, a primeira execução gera uma base sem registros e um CSV apenas com cabeçalho. Em uma base já carregada, aplica-se a regra de retenção descrita em Assumptions.

## Requirements

### Functional Requirements

- **FR-001** — Percorrer automaticamente todas as páginas da listagem geral do catálogo a partir de sua entrada pública e reconhecer o fim da paginação. Uma página necessária indisponível após a aplicação da regra de tentativas de FR-007, quando aplicável, ou um ciclo de paginação caracteriza falha de cobertura.
- **FR-002** — Coletar cinco campos obrigatórios por livro. Preservar o título completo e o significado do preço, da disponibilidade e da avaliação exibidos na fonte. Quando a listagem e a página de detalhe exibirem valores válidos, mas diferentes, para preço, disponibilidade ou avaliação, usar o valor da página de detalhe para cada campo divergente. Registrar a URL da página de detalhe.
- **FR-003** — Validar e padronizar cada livro antes de armazená-lo. Exigir título com conteúdo após remoção dos espaços nas extremidades, preço decimal não negativo em libras esterlinas com duas casas, disponibilidade como `em estoque` ou `sem estoque`, avaliação inteira de 1 a 5 e URL absoluta válida do detalhe no domínio do catálogo. Resolver links relativos e remover parâmetros de consulta e fragmentos da URL. Rejeitar registros com qualquer campo inválido ou ausente.
- **FR-004** — Gravar os registros válidos em um banco SQLite local consultável após a execução.
- **FR-005** — Após a gravação bem-sucedida da base, gerar um CSV local em UTF-8 com cabeçalho, os cinco campos e uma linha por registro armazenado. Adaptar somente a representação no CSV dos títulos que possam ser interpretados como fórmulas para que sejam exibidos como texto nos leitores de planilha documentados. Preservar na base o título padronizado conforme FR-003. Substituir o arquivo anterior quando o novo estiver completo.
- **FR-006** — Usar a URL padronizada do detalhe como identidade do livro tanto na primeira carga quanto nas seguintes. Inserir URLs novas, atualizar os campos de URLs já armazenadas quando os dados válidos mudarem e manter uma única linha por URL, inclusive em repetições na mesma coleta.
- **FR-007** — Registrar cada erro detectado com a etapa e a causa disponível, incluindo livro, página ou destino afetado quando identificável. Em caso de falha de conexão, fazer até três tentativas no total por página da listagem ou de detalhe, incluindo a tentativa inicial, e parar de tentar assim que a leitura for bem-sucedida. Se a terceira tentativa falhar na listagem, encerrar a coleta conforme FR-010. Se a falha estiver restrita ao detalhe de um livro após as tentativas aplicáveis, rejeitar o livro e prosseguir com os demais.
- **FR-008** — Apresentar, ao fim de cada execução, um resumo com estado geral (sucesso, conclusão com erros de itens ou falha), estado da gravação da base e da exportação, páginas percorridas, ocorrências de livros detectadas, itens rejeitados, duplicatas na coleta, registros inseridos, atualizados e mantidos sem mudança, linhas exportadas e total de erros. Indicar falha de qualidade dos dados quando a listagem for percorrida por completo e todos os livros detectados forem rejeitados. Contabilizar apenas gravações e exportações concluídas na execução corrente.
- **FR-009** — Permitir execução local com acesso à internet para consultar a fonte pública, usando ferramentas e serviços gratuitos. Disponibilizar em português as instruções de configuração, execução, interpretação do resumo e execução dos testes. Identificar no guia os leitores de planilha nos quais a abertura do CSV com títulos protegidos é verificada e como abrir o arquivo nesses leitores.
- **FR-010** — Preservar a base e o arquivo anteriores em caso de falha de cobertura, de qualidade dos dados ou de gravação da base. Em caso de falha de qualidade dos dados, manter ausente qualquer saída que ainda não exista. Quando a gravação da base for concluída e a exportação falhar, manter a base gravada e preservar o CSV anterior, se houver. Informar no resumo em que etapa houve falha e quais saídas estão disponíveis e atualizadas.

### Key Entities

- **Livro** — Item do catálogo com título, preço em libras, disponibilidade, avaliação e URL padronizada da página de detalhe, que identifica o registro.
- **Execução** — Uma passagem de coleta, validação, armazenamento e exportação com resultado, contagens e registros de erro.
- **Exportação** — Arquivo tabular que representa o conjunto de livros armazenados ao fim da última exportação concluída.

A entrega segue os dez princípios e as regras de desenvolvimento da [constituição v1.0.0](../../.specify/memory/constitution.md).

## Success Criteria

### Measurable Outcomes

- **SC-001** — Em um catálogo estável e acessível, uma execução a partir de uma base vazia, iniciada uma só vez e sem intervenção durante a coleta, percorre 100% das páginas da listagem geral e disponibiliza 100% dos livros válidos, inclusive os da última página.
- **SC-002** — Em um catálogo de referência com valores válidos e inválidos conhecidos, 100% dos livros válidos armazenados apresentam os cinco campos com valores corretos. Todo valor válido de preço, disponibilidade ou avaliação que divergir entre a listagem e a página de detalhe corresponde ao valor da página de detalhe. Nenhum registro inválido novo é gravado.
- **SC-003** — Após duas execuções sobre o mesmo catálogo, a contagem de livros permanece igual e há zero URLs duplicadas. Ao mudar um único campo válido de um livro existente, a execução seguinte atualiza exatamente um registro desse livro.
- **SC-004** — Após uma exportação concluída, 100% dos registros armazenados têm uma linha correspondente no arquivo e os cinco campos representam os valores da base. Nos leitores de planilha documentados, todos os títulos de referência que poderiam ser interpretados como fórmula são exibidos como texto sem avaliação de fórmula.
- **SC-005** — Em execuções de referência que cubram sucesso, rejeição de um livro e falhas de paginação, qualidade dos dados, armazenamento e exportação, todos os resumos informam corretamente o estado da execução e das saídas. Cada falha simulada é registrada com sua etapa e causa disponível. Uma conexão restabelecida até a terceira tentativa permite processar a página. Três falhas de conexão na mesma página resultam em falha de cobertura na listagem ou em rejeição do livro no detalhe. Uma falha de qualidade dos dados deixa as saídas anteriores intactas e gera zero novas saídas.
- **SC-006** — Uma pessoa operadora consegue seguir o guia em português e concluir a coleta, conferir os resultados e abrir o arquivo exportado em uma sessão local, seguindo as instruções fornecidas e sem contratar serviços.
- **SC-007** — Antes da aprovação da primeira versão do pipeline, todos os testes locais com catálogo de referência devem passar sem acesso à internet. Esses testes verificam a cobertura da paginação, as regras de dados, a atualização sem duplicatas, a exportação, os resumos e a preservação das saídas em caso de falha. A aprovação também exige pelo menos uma execução no site público com cobertura completa da listagem geral, resumo de sucesso, base gravada e exportação concluída.

## Assumptions

- O escopo cobre a listagem geral do catálogo e os detalhes de seus livros. Páginas de categoria, outras fontes, agendamento e histórico de preços ficam fora desta entrega.
- A coleta real requer acesso à internet. Nos testes locais, a cobertura é comparada com um catálogo de referência estável e disponível sem internet. Na verificação obrigatória no site público, a cobertura é comparada com a listagem disponível no momento da execução.
- Disponibilidade representa a condição de estoque, com dois valores possíveis. A quantidade em estoque fica fora do escopo.
- Se a mesma URL aparecer várias vezes na mesma coleta, vale a primeira ocorrência válida. As ocorrências válidas seguintes contam como duplicatas.
- Novas coletas atualizam os valores válidos de livros conhecidos. Livros ausentes na fonte ou rejeitados em uma execução posterior mantêm seus últimos valores válidos na base. O arquivo exportado representa a base local, incluindo esses registros.
