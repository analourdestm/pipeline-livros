# Implementation Plan: Coletar o catálogo de livros

**Branch** — `main` · **Data** — 2026-11-24 · **Especificação** — [spec.md](spec.md)

## Summary

Uma CLI local percorre a listagem geral do Books to Scrape, extrai os campos das páginas de detalhe, valida livros e resolve duplicatas. Após confirmar a cobertura, grava o lote em SQLite, exporta o conteúdo confirmado para CSV e apresenta um resumo em português. A execução preserva as saídas conforme a etapa em que ocorrer uma falha.

## Technical Context

| Aspecto | Escolha |
| --- | --- |
| Linguagem | CPython 3.14.x em ambiente virtual `.venv` |
| Dependências de execução | Requests para HTTP, Beautiful Soup com `html.parser` para extração |
| Biblioteca padrão | `argparse`, `logging`, `dataclasses`, `decimal`, `urllib.parse`, `sqlite3`, `csv`, `pathlib`, `fcntl`, `tempfile` e `os` |
| Armazenamento | SQLite local e CSV UTF-8 |
| Testes | Pytest sem rede para a suíte local. Coleta pública e abertura no LibreOffice Calc para validação da primeira versão |
| Plataforma | macOS com Apple Silicon ou Intel e Python do Python.org |
| Tipo de projeto | CLI em um único pacote Python |
| Escala e desempenho | Catálogo de aproximadamente mil livros na referência observada. Uma execução serial, uma requisição ativa por vez e lote validado em memória. A meta é cobertura completa com tentativas limitadas |
| Restrições | Internet apenas para a coleta real e preparação inicial do ambiente. Ferramentas gratuitas e uma execução ativa por diretório de saída |

As justificativas, os limites de rede e as fontes consultadas estão em [research.md](research.md).

## Constitution Check

Avaliação inicial e reavaliação após o desenho técnico com base na [constituição v1.0.0](../../.specify/memory/constitution.md).

| Princípios | Inicial | Após o desenho | Evidência |
| --- | --- | --- | --- |
| I e II — Python, simplicidade e modularidade | Conforme | Conforme | Pacote único, CLI fina e responsabilidades explícitas |
| III — Separação das etapas | Conforme | Conforme | Extração entrega dados brutos, transformação entrega livros válidos, carga confirma a base e exportação consome o resultado confirmado |
| IV — Ferramentas gratuitas | Conforme | Conforme | Execução e testes locais com dependências gratuitas. Finalidade de cada dependência e limites operacionais em research.md |
| V — Testes unitários | Conforme | Conforme | Testes isolados de cada etapa, integração offline e teste de regressão quando regras de dados mudarem |
| VI e VII — Erros, qualidade e unicidade | Conforme | Conforme | Logging por etapa, validação antes da escrita e chave única no SQLite |
| VIII — Documentação em português | Conforme | Conforme | Guia de validação e contratos descrevem configuração, execução, formatos e testes |
| IX — Git | Conforme | Conforme | Código, testes e documentação serão versionados conforme o fluxo do projeto. A etapa Plan produz os documentos listados abaixo |
| X — Legibilidade para iniciantes | Conforme | Conforme | Funções diretas, tipos de dados simples e fluxo explícito na orquestração |

## Project Structure

### Documentation (this feature)

```text
specs/001-coletar-catalogo-livros/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── cli.md
    └── csv.md
```

### Source Code (repository root)

Estrutura proposta para a implementação.

```text
pipeline_livros/
├── __init__.py
├── __main__.py
├── pipeline.py
├── extracao.py
├── transformacao.py
├── armazenamento.py
└── exportacao.py
tests/
├── unit/
├── integration/
└── fixtures/
    └── catalogo/
pyproject.toml
README.md
.gitignore
```

**Decisão de estrutura.** Um pacote na raiz permite executar `python -m pipeline_livros` na raiz do repositório. `pyproject.toml` declara a versão de Python e as dependências. O README documenta a operação em português. O Git ignora o ambiente virtual, caches e o diretório padrão de saída.

## Arquitetura ETL e responsabilidades

| Módulo | Entrada e responsabilidade | Saída |
| --- | --- | --- |
| `__main__.py` | Interpretar a CLI com `argparse`, configurar `logging`, chamar o pipeline, exibir o resumo e concluir com o código de saída contratado | Resumo e código de saída |
| `extracao.py` | Ler páginas com Requests, verificar destinos, aplicar a política de conexão e extrair do HTML links, paginação e campos brutos | Página da listagem ou detalhe bruto, com contexto para diagnóstico |
| `transformacao.py` | Validar campos, normalizar URL e converter preço, estoque e estrelas | Livro tratado ou motivo de rejeição |
| `armazenamento.py` | Criar ou atualizar a tabela SQLite com valores parametrizados, classificar mudanças e consultar os dados confirmados | Contagens confirmadas e linhas ordenadas por URL |
| `exportacao.py` | Converter preços para libras, aplicar proteção aos títulos no CSV e publicar o arquivo completo | Contagem de linhas publicadas |
| `pipeline.py` | Percorrer as páginas na ordem da fonte, guardar o primeiro livro válido de cada URL, controlar o bloqueio e as transições, registrar diagnósticos e reunir as contagens | Resultado da execução conforme o contrato CLI |

A extração resolve e valida links antes do GET. A transformação usa a mesma normalização de URL de detalhe para a chave do livro. Campos de preço, estoque e avaliação vêm do detalhe, inclusive quando a listagem diverge. Campo obrigatório inválido ou ausente no detalhe rejeita o livro. Cada cartão detectado conta como ocorrência, mesmo quando o link do livro estiver ausente.

A paginação aceita a entrada geral e as páginas `/catalogue/page-N.html`. Variações conhecidas da URL da primeira página têm a mesma identidade para detectar ciclos. A extração valida a progressão quando há indicador e requer evidência de última página, de catálogo de página única ou de vazio explícito. Quando a fonte informa o total de itens, compara esse total com as ocorrências detectadas, antes de deduplicar. Uma listagem irreconhecível ou uma contagem incompatível é falha de cobertura.

O pipeline acumula livros válidos em memória e só abre a base para escrita depois de concluir a listagem e aplicar a regra de qualidade. A primeira carga prepara a base em um temporário no mesmo diretório, confirma a transação, fecha a conexão e publica o arquivo SQLite com substituição atômica. A configuração padrão de journal do SQLite mantém a publicação limitada ao arquivo confirmado. Nas cargas seguintes, uma transação explícita cobre o lote e qualquer criação de estrutura necessária. A exportação lê a base confirmada, publica um temporário completo com substituição atômica e limpa temporários em falhas tratadas. O bloqueio do diretório é mantido até concluir a publicação e é liberado pelo fechamento do descritor. Um arquivo de bloqueio persistente permite que todas as invocações disputem o mesmo bloqueio.

## Tratamento de falhas

| Evento | Resposta |
| --- | --- |
| Timeout ou falha transitória de conexão | Até três tentativas no total por página. Registrar a tentativa, a causa e se houve recuperação |
| Página da listagem indisponível, fora da origem permitida, em ciclo ou com paginação inconsistente | Encerrar com falha de cobertura e preservar as saídas |
| Detalhe ilegível, link inválido ou campo inválido | Registrar a rejeição, preservar o livro anterior e continuar com os demais |
| Listagem completa com livros e nenhum livro válido | Encerrar com falha de qualidade, preservar saídas existentes e manter ausentes as demais |
| Catálogo explicitamente vazio | Concluir normalmente. Exportar os registros retidos ou apenas o cabeçalho quando a base estiver vazia |
| Erro de escrita SQLite | Reverter a transação, manter saídas anteriores e informar falha de armazenamento |
| Erro de CSV após gravar o SQLite | Manter o SQLite confirmado, preservar o CSV anterior e informar se ele está ausente ou desatualizado |
| Diretório ocupado por outra execução | Encerrar antes da coleta e registrar falha de preparação, com saídas existentes preservadas |

Cada diagnóstico identifica etapa, causa e página, livro ou destino quando disponíveis. URLs registradas usam a forma canônica ou uma descrição segura do link recusado. O total de erros inclui tentativas de conexão malsucedidas e desfechos definitivos. Tentativas recuperadas aparecem em um subtotal de diagnóstico e a página segue para processamento. O [contrato da CLI](contracts/cli.md) define a relação entre eventos, estados e contagens.

## Estratégia de testes

| Nível | Cobertura |
| --- | --- |
| Unitário, extração | Paginação, links relativos e inválidos, HTML malformado, detalhe, codificação, timeout, recuperação e três tentativas esgotadas |
| Unitário, transformação | Campos obrigatórios, preço em pence, disponibilidade, estrelas, título completo e precedência do detalhe, identidade por URL |
| Unitário, armazenamento e exportação | Inserção e atualização, transação e reversão, CSV UTF-8, cabeçalho, aplicação seletiva da proteção de títulos, substituição e erro de escrita |
| Integração offline | Catálogo multipágina simulado, SQLite e CSV reais em diretório temporário, comparação por URL e por campo, reprocessamento, preservação em falhas, bloqueio e conferência de eventos no resumo e no log |
| Validação de entrega | Uma coleta completa no site público comparada com um inventário independente da fonte, e abertura no Calc de um CSV gerado a partir de títulos sintéticos |

A suíte offline bloqueia HTTP real, simula respostas e espera por novas tentativas sem atrasos reais. Os testes verificam o estado dos arquivos existentes e ausentes, os indicadores do resumo e os registros de erro. A matriz de validação e os comandos previstos estão em [quickstart.md](quickstart.md).
