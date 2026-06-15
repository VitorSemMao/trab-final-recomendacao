# Decisoes de Design

Este documento resume as principais decisoes tecnicas do projeto.

## Dataset

- O projeto usa o MovieLens 100K porque e um dataset classico, pequeno e bem documentado.
- Foi mantido um fallback local para que a API continue funcional mesmo sem download externo.

## Modelo de recomendacao

- A primeira fase usa filtragem baseada em conteudo, aproveitando preferencias e tags dos filmes.
- A etapa seguinte adiciona feedback do usuario e similaridade entre usuarios para formar uma abordagem hibrida.
- O score final combina o componente de conteudo com o componente colaborativo em uma proporcao fixa.
- Para usuarios sem preferencias e sem historico, o sistema usa um fallback explicito de filmes populares com score bayesiano.

## API

- A API foi feita em FastAPI para aproveitar validacao, tipagem e Swagger UI automatico.
- Os endpoints cobrem usuarios, filmes, preferencias, avaliacoes, recomendacoes, listagem, busca e popularidade, conforme o PDF e os refinamentos feitos no projeto.
- O endpoint `GET /dataset` ajuda na demonstracao do estado atual do sistema, informando a origem do catalogo e os totais carregados.

## Persistencia

- O projeto passou a usar SQLite para persistir usuarios, preferencias, filmes adicionados manualmente e avaliacoes.
- SQLite foi escolhido por ser leve, nativo do Python e simples de executar tanto localmente quanto no Docker, sem depender de um servidor externo.
- O catalogo base continua vindo do MovieLens 100K; a camada SQLite complementa esse catalogo com os dados gerados durante o uso da API.

## Docker e execucao

- O `docker-compose.yml` monta `./data` para manter o dataset fora da imagem.
- O banco SQLite tambem fica em `./data`, o que preserva os dados entre reinicializacoes do container.
- O script de download do MovieLens evita baixar novamente quando os arquivos ja existem.
- Os scripts Bash foram pensados para uso facil no Git Bash do Windows.

## Testes

- Os testes validam a saude da API, o cadastro basico e o comportamento do motor hibrido.
- Ha cobertura especifica para garantir que os dados persistidos em SQLite sejam recarregados corretamente em uma nova inicializacao do servico.
- Os testes tambem cobrem fluxos de erro, cold start e rotas de consulta do catalogo.
- Essa cobertura e suficiente para demonstrar que a aplicacao funciona e que a recomendacao reage a feedback do usuario.

## Avaliacao

- O projeto inclui um script de avaliacao simples com `precision@k` e `hit rate@k` sobre o MovieLens 100K.
- Essa etapa foi adicionada para dar uma validacao numerica minima ao recomendador, complementando a demonstracao via API.
