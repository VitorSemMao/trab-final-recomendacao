# Dataset escolhido

O dataset principal do projeto e o [MovieLens 100K](https://grouplens.org/datasets/movielens/100k/), publicado pelo GroupLens.

## Por que este dataset

- E um benchmark classico para sistemas de recomendacao.
- E pequeno o suficiente para desenvolvimento rapido.
- Tem metadados de filmes e avaliacoes de usuarios.
- Funciona bem para uma primeira versao content-based e para evoluir depois para filtragem colaborativa.

## Como baixar

Use o script do projeto:

```bash
python scripts/download_movielens_100k.py
```

O script baixa o arquivo oficial `ml-100k.zip` e extrai os arquivos no diretorio `data/movielens-100k/`.

## Fallback local

Se o dataset ainda nao estiver presente, a aplicacao usa um catalogo pequeno interno para manter a API funcional durante o desenvolvimento.

## Uso no motor de recomendacao

- As preferencias do usuario ajudam a montar o perfil inicial.
- As notas recebidas em `POST /users/{user_id}/ratings` alimentam a parte colaborativa do ranking.
- Filmes ja avaliados pelo proprio usuario sao removidos das recomendacoes para evitar repeticao.
