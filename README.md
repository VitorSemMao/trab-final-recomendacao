# Sistema de Recomendacao com FastAPI e Docker

Repositorio inicial do trabalho "Desenvolvimento de um Sistema de Recomendacao".

## O que o PDF pede

- Escolha de um dataset publico ou fornecido pelo professor.
- Implementacao de um modelo de recomendacao com filtragem colaborativa, baseada em conteudo ou hibrida.
- Criacao de uma API com FastAPI para:
  - adicionar usuarios e itens
  - obter recomendacoes para um usuario
  - atualizar preferencias de um usuario
- Containerizacao com Docker e, se necessario, `docker-compose`.
- Documentacao automatica via Swagger UI.
- Testes unitarios e de integracao.

## Estado atual

- Estrutura inicial do projeto.
- API minima em FastAPI.
- Base para Docker e testes.
- Plano de entregas a cada 2 dias ate 22/06/2026.

## Roadmap curto

- 01/06 a 02/06: organizar o repo, ler o PDF e definir o escopo.
- 03/06 a 04/06: escolher o dataset e preparar o ambiente.
- 05/06 a 06/06: montar a base da API e a estrutura do projeto.
- 07/06 a 08/06: criar a primeira versao do modelo de recomendacao.
- 09/06 a 10/06: integrar o modelo aos endpoints da API.
- 11/06 a 12/06: adicionar Dockerfile e `docker-compose.yml`.
- 13/06 a 14/06: escrever testes unitarios e de integracao.
- 15/06 a 16/06: melhorar a documentacao e exemplos de uso.
- 17/06 a 18/06: ajustar qualidade, validacoes e casos de erro.
- 19/06 a 20/06: revisar tudo e corrigir falhas finais.
- 21/06 a 22/06: preparar a demonstracao final para o professor.

## Como rodar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Como rodar com Docker

```bash
docker compose up --build
```
