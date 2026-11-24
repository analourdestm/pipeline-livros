<!--
Relatório de impacto de sincronização
- Versão: modelo sem versão → 1.0.0 (adoção inicial).
- Princípios: dez princípios estabelecidos (I a X).
- Seções preenchidas: Core Principles, Restrições técnicas, Fluxo de desenvolvimento e Governance.
- Seções removidas: nenhuma.
- Pendências: nenhuma.
-->

# Pipeline de Livros Constitution

## Core Principles

### I. Python como linguagem principal

O código que executa as etapas do pipeline deve ser escrito em Python.

### II. Arquitetura simples e modular

Cada módulo deve ter uma responsabilidade clara. Toda nova camada ou abstração deve
resolver uma necessidade concreta do pipeline.

### III. Separação das etapas do pipeline

A extração, a transformação e o armazenamento devem ficar em módulos distintos.
A extração lê as fontes, a transformação valida e prepara os dados, e o armazenamento
persiste os resultados. Cada etapa deve ter entradas e saídas definidas para permitir
testes isolados.

### IV. Ferramentas gratuitas

O desenvolvimento, os testes e a execução do pipeline devem ser possíveis com ferramentas
e serviços gratuitos.

### V. Testes unitários

Cada etapa deve ter testes unitários que verifiquem seu comportamento de forma isolada.
Mudanças nas regras de transformação ou validação devem incluir testes para os casos
afetados.

### VI. Registro de erros

O pipeline deve registrar os erros ocorridos durante a execução, identificando a etapa
e a causa disponível para facilitar o diagnóstico.

### VII. Qualidade e unicidade dos dados

O pipeline deve validar os campos obrigatórios, os tipos e as regras de negócio antes
do armazenamento. Cada conjunto de dados deve ter um critério explícito de unicidade,
aplicado tanto na carga inicial quanto no reprocessamento.

### VIII. Documentação em português

O guia do projeto e as instruções de configuração, execução e testes devem ser escritos
em português e atualizados quando o procedimento mudar.

### IX. Versionamento com Git

O código, os testes e a documentação devem ser versionados com Git. Cada commit deve
descrever a mudança que registra.

### X. Código legível para iniciantes

O código deve usar nomes descritivos, funções com responsabilidades claras e fluxo de
controle explícito para que uma pessoa iniciante em Python consiga acompanhá-lo.

## Restrições técnicas

Toda nova dependência deve ter sua finalidade documentada. Se um serviço tiver plano
gratuito com limites de uso, o projeto deve documentar os limites relevantes para a
execução do pipeline.

## Fluxo de desenvolvimento

Antes de integrar uma alteração, a revisão deve verificar a conformidade com os
princípios aplicáveis e confirmar que os testes unitários passam. Mudanças nas regras
de qualidade devem atualizar os testes e a documentação correspondentes.

## Governance

A constituição orienta as especificações, os planos e as revisões do projeto. Cada
alteração na constituição deve registrar a justificativa e o impacto sobre o trabalho
existente, receber aprovação das pessoas responsáveis pelo projeto e atualizar a versão
e a data da última alteração.

O versionamento segue `MAJOR.MINOR.PATCH`. Uma mudança incompatível com as regras
vigentes incrementa `MAJOR`. Um novo princípio ou uma ampliação compatível incrementa
`MINOR`. Correções e esclarecimentos que preservam as obrigações incrementam `PATCH`.

**Versão**: 1.0.0 | **Ratificação**: 2026-11-24 | **Última alteração**: 2026-11-24
