# Avaliacao simples do recomendador

Para complementar a demonstracao da API, o projeto inclui uma avaliacao simples baseada no MovieLens 100K.

## Objetivo

A ideia e sair de uma demonstracao apenas visual e gerar uma medida numerica basica do comportamento do recomendador.

## Estrategia usada

- O script carrega o catalogo do MovieLens 100K e o historico bruto de avaliacoes por usuario.
- Para cada usuario elegivel, uma avaliacao positiva recente e separada como item de teste.
- As demais avaliacoes ficam como historico de treinamento dentro do servico.
- O recomendador gera o top-k de cada usuario e a avaliacao mede se o filme separado aparece nessas recomendacoes.

## Metricas calculadas

- `precision@k`: proporcao de acertos dentro da lista de tamanho `k`.
- `hit rate@k`: proporcao de usuarios em que o filme separado apareceu no top-k.

## Como executar

```bash
python scripts/evaluate_recommender.py
```

## Observacao

Essa avaliacao nao substitui um protocolo completo de experimentacao, mas ja ajuda a dar um carater mais academico ao trabalho e mostra que o sistema pode ser analisado alem da interface da API.
