# Decisoes de Design

Este documento resume as principais decisoes tecnicas do projeto.

## Dataset

- O projeto usa o MovieLens 100K porque e um dataset classico, pequeno e bem documentado.
- Foi mantido um fallback local para que a API continue funcional mesmo sem download externo.

## Modelo de recomendacao

- A primeira fase usa filtragem baseada em conteudo, aproveitando preferencias e tags dos filmes.
- A etapa seguinte adiciona feedback do usuario e similaridade entre usuarios para formar uma abordagem hibrida.
- O score final combina o componente de conteudo com o componente colaborativo em uma proporcao fixa.

## API

- A API foi feita em FastAPI para aproveitar validacao, tipagem e Swagger UI automatico.
- Os endpoints cobrem usuarios, filmes, preferencias, avaliacoes e recomendacoes, conforme o PDF.
- O endpoint `GET /dataset` ajuda na demonstracao do estado atual do sistema, informando a origem do catalogo e os totais carregados.

## Persistencia

- A persistencia foi propositalmente mantida em memoria nesta fase para simplificar a entrega inicial.
- As avaliacoes e preferencias sao suficientes para demonstrar o comportamento do motor sem introduzir um banco de dados antes do necessario.

## Docker e execucao

- O `docker-compose.yml` monta `./data` para manter o dataset fora da imagem.
- O script de download do MovieLens evita baixar novamente quando os arquivos ja existem.
- Os scripts Bash foram pensados para uso facil no Git Bash do Windows.

## Testes

- Os testes validam a saude da API, o cadastro basico e o comportamento do motor hibrido.
- Essa cobertura e suficiente para demonstrar que a aplicacao funciona e que a recomendacao reage a feedback do usuario.
