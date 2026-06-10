# Sistema de Recomendacao de Filmes com FastAPI

API REST para cadastro de usuarios e filmes, coleta de preferencias e notas, e geracao de recomendacoes personalizadas.

O projeto foi desenvolvido como trabalho academico de sistema de recomendacao e utiliza o dataset [MovieLens 100K](https://grouplens.org/datasets/movielens/100k/) quando disponivel. Caso o dataset nao esteja presente localmente, a aplicacao continua operando com um catalogo reduzido de fallback para facilitar demonstracoes e testes.

## Visao geral

- API REST em FastAPI com documentacao automatica em `/docs` e `/redoc`.
- Recomendacao hibrida baseada em perfil de conteudo e similaridade entre usuarios.
- Suporte a cadastro de usuarios, cadastro de filmes, atualizacao de preferencias, registro de notas e consulta de recomendacoes.
- Execucao local ou via Docker com download automatizado do MovieLens 100K.
- Suite de testes cobrindo saude da API e comportamento do motor de recomendacao.

## Arquitetura resumida

```text
Cliente HTTP
   |
   v
FastAPI (app/main.py)
   |
   v
RecommendationService (app/service.py)
   |-- Perfil do usuario por preferencias e notas
   |-- Similaridade entre usuarios
   `-- Ranking final das recomendacoes
   |
   v
Dataset loader (app/dataset.py)
   |-- MovieLens 100K
   `-- Catalogo de fallback
```

## Modelo de recomendacao

O motor atual combina dois sinais:

1. Conteudo: usa as preferencias informadas pelo usuario e as tags dos filmes ja avaliados para montar um perfil de interesse.
2. Colaborativo: usa similaridade cosseno entre usuarios com filmes em comum para reforcar filmes bem avaliados por perfis parecidos.

O score final hoje segue a proporcao implementada em `app/service.py`:

```text
score_final = (content_score * 0.7) + (collaborative_score * 0.3)
```

Regras importantes da implementacao atual:

- filmes ja avaliados pelo usuario nao aparecem nas recomendacoes;
- notas podem variar de `0` a `5`;
- sem dataset local, a API sobe com um pequeno catalogo de exemplo;
- os dados de usuarios e avaliacoes ficam em memoria nesta fase do projeto.

## Estrutura do projeto

```text
trab-final-recomendacao/
|-- app/
|   |-- __init__.py
|   |-- dataset.py         # carregamento do MovieLens e fallback local
|   |-- main.py            # endpoints FastAPI
|   |-- schemas.py         # modelos de entrada e saida
|   `-- service.py         # motor de recomendacao
|-- docs/
|   |-- dataset.md
|   |-- decisions.md
|   `-- roadmap.md
|-- scripts/
|   |-- download_movielens_100k.py
|   |-- install.sh
|   |-- run.sh
|   `-- test.sh
|-- tests/
|   |-- test_health.py
|   `-- test_recommender.py
|-- Dockerfile
|-- docker-compose.yml
`-- requirements.txt
```

## Pre-requisitos

### Execucao local

- Python 3.11+
- `pip`
- Git Bash no Windows para usar os scripts `.sh`

### Execucao em container

- Docker
- Docker Compose

## Instalacao e execucao

### Scripts prontos

```bash
bash scripts/install.sh
bash scripts/run.sh
bash scripts/test.sh
```

### Rodando localmente

```bash
python -m pip install -r requirements.txt
python scripts/download_movielens_100k.py
python -m uvicorn app.main:app --reload
```

### Rodando com Docker

```bash
docker compose up --build
```

No fluxo com Docker, o volume `./data` e montado dentro do container e a inicializacao tenta baixar o MovieLens 100K automaticamente. Se o download falhar, a API continua funcionando com o catalogo de fallback.

### Acessos uteis

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## Endpoints da API

| Metodo | Endpoint | Descricao |
| --- | --- | --- |
| `GET` | `/` | Retorna metadados simples sobre a fase atual do projeto |
| `GET` | `/health` | Verifica se a API esta respondendo |
| `GET` | `/dataset` | Informa a origem do catalogo, o total de filmes e usuarios registrados |
| `POST` | `/users` | Cria um usuario com nome e preferencias opcionais |
| `PUT` | `/users/{user_id}/preferences` | Atualiza as preferencias do usuario |
| `POST` | `/movies` | Adiciona um filme manualmente ao catalogo |
| `POST` | `/users/{user_id}/ratings` | Registra ou atualiza a nota de um filme |
| `GET` | `/users/{user_id}/recommendations?limit=5` | Retorna recomendacoes personalizadas |

## Exemplos de uso

### Criar usuario

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Vitor\", \"preferences\": [\"Sci-Fi\", \"Action\"]}"
```

### Avaliar um filme

```bash
curl -X POST http://localhost:8000/users/1/ratings \
  -H "Content-Type: application/json" \
  -d "{\"movie_id\": 50, \"rating\": 5}"
```

### Buscar recomendacoes

```bash
curl "http://localhost:8000/users/1/recommendations?limit=5"
```

### Consultar dataset carregado

```bash
curl http://localhost:8000/dataset
```

## Testes

Para executar a suite:

```bash
python -m pytest -q
```

Ou via script:

```bash
bash scripts/test.sh
```

A validacao atual cobre:

- endpoint de saude;
- endpoint raiz;
- criacao de usuario;
- atualizacao de preferencias;
- influencia das notas no ranking hibrido.

## Documentacao complementar

- [Dataset escolhido](docs/dataset.md)
- [Decisoes de design](docs/decisions.md)
- [Roadmap do projeto](docs/roadmap.md)

## Limitacoes atuais

- persistencia apenas em memoria;
- sem autenticacao ou controle de sessao;
- recomendacao baseada em tags e historico simples, sem pipeline de treinamento offline;
- API focada no escopo academico do trabalho.
