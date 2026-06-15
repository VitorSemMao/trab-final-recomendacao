# Sistema de Recomendacao de Filmes com FastAPI

API REST para cadastro de usuarios e filmes, coleta de preferencias e notas, e geracao de recomendacoes personalizadas.

O projeto foi desenvolvido como trabalho academico de sistema de recomendacao e utiliza o dataset [MovieLens 100K](https://grouplens.org/datasets/movielens/100k/) quando disponivel. Caso o dataset nao esteja presente localmente, a aplicacao continua operando com um catalogo reduzido de fallback para facilitar demonstracoes e testes.

## Visao geral

- API REST em FastAPI com documentacao automatica em `/docs` e `/redoc`.
- Recomendacao hibrida baseada em perfil de conteudo e similaridade entre usuarios.
- Suporte a cadastro de usuarios, cadastro de filmes, atualizacao de preferencias, registro de notas e consulta de recomendacoes.
- Endpoints para listar filmes, buscar por titulo, consultar filmes populares e ver o historico de notas do usuario.
- Persistencia local com SQLite para usuarios, filmes criados manualmente e avaliacoes.
- Execucao local ou via Docker com download automatizado do MovieLens 100K.
- Script de avaliacao simples com `precision@k` e `hit rate@k` sobre o MovieLens 100K.
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
SQLite (app/storage.py)
   |-- Usuarios
   |-- Filmes criados na API
   `-- Avaliacoes registradas
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
- usuarios sem preferencias e sem historico recebem fallback explicito de filmes populares;
- notas podem variar de `0` a `5`;
- usuarios, filmes criados manualmente e avaliacoes ficam salvos em SQLite;
- sem dataset local, a API sobe com um pequeno catalogo de exemplo;
- os filmes base continuam vindo do MovieLens 100K ou do catalogo de fallback.

## Estrutura do projeto

```text
trab-final-recomendacao/
|-- app/
|   |-- __init__.py
|   |-- dataset.py         # carregamento do MovieLens e fallback local
|   |-- main.py            # endpoints FastAPI
|   |-- schemas.py         # modelos de entrada e saida
|   |-- service.py         # motor de recomendacao
|   `-- storage.py         # persistencia SQLite
|-- docs/
|   |-- dataset.md
|   |-- decisions.md
|   `-- roadmap.md
|-- scripts/
|   |-- download_movielens_100k.py
|   |-- evaluate_recommender.py
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
python scripts/evaluate_recommender.py
```

### Rodando localmente

```bash
python -m pip install -r requirements.txt
python scripts/download_movielens_100k.py
python -m uvicorn app.main:app --reload
```

O banco SQLite e criado automaticamente em `data/recommendation.db`. Se quiser alterar o local do arquivo, use a variavel de ambiente `RECOMMENDER_DB_PATH`.

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
| `GET` | `/users/{user_id}/ratings` | Lista as notas registradas por um usuario |
| `PUT` | `/users/{user_id}/preferences` | Atualiza as preferencias do usuario |
| `GET` | `/movies` | Lista filmes e permite busca por titulo ou tag via `q` |
| `GET` | `/movies/{movie_id}` | Retorna os detalhes de um filme |
| `POST` | `/movies` | Adiciona um filme manualmente ao catalogo |
| `GET` | `/movies/popular` | Retorna os filmes populares para demonstracao e cold start |
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

### Listar filmes populares

```bash
curl "http://localhost:8000/movies/popular?limit=5"
```

### Buscar filmes por titulo

```bash
curl "http://localhost:8000/movies?q=matrix&limit=5"
```

### Consultar notas de um usuario

```bash
curl "http://localhost:8000/users/1/ratings"
```

### Consultar dataset carregado

```bash
curl http://localhost:8000/dataset
```

## Avaliacao do recomendador

Para gerar uma validacao simples com base no MovieLens 100K:

```bash
python scripts/evaluate_recommender.py
```

O script monta usuarios de avaliacao a partir do historico do MovieLens, separa um filme positivo como holdout e calcula:

- `precision@k`
- `hit rate@k`

Essa etapa ajuda a justificar o comportamento do recomendador de forma mais academica, mesmo sem um pipeline de treino offline mais pesado.

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
- listagem, busca e consulta de filmes;
- fluxo de filmes populares para cold start;
- historico de notas do usuario;
- erros de usuario inexistente, filme inexistente e nota invalida;
- avaliacao simples do recomendador;
- criacao de usuario;
- persistencia em SQLite entre reinicializacoes;
- atualizacao de preferencias;
- influencia das notas no ranking hibrido.

## Documentacao complementar

- [Dataset escolhido](docs/dataset.md)
- [Decisoes de design](docs/decisions.md)
- [Avaliacao simples do recomendador](docs/evaluation.md)
- [Roadmap do projeto](docs/roadmap.md)

## Limitacoes atuais

- sem autenticacao ou controle de sessao;
- recomendacao baseada em tags e historico simples, sem pipeline de treinamento offline;
- apenas usuarios, filmes criados na API e avaliacoes sao persistidos; o catalogo base continua vindo do dataset em arquivo;
- API focada no escopo academico do trabalho.
