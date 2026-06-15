from fastapi import FastAPI, HTTPException, Query
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from .schemas import (
    DatasetRead,
    MovieCreate,
    MovieRead,
    PreferenceUpdate,
    RatingCreate,
    RatingRead,
    RecommendationRead,
    UserMovieRatingRead,
    UserCreate,
    UserRead,
)
from .service import RecommendationService


def create_app(service: RecommendationService | None = None) -> FastAPI:
    recommender = service or RecommendationService()
    app = FastAPI(title="Sistema de Recomendacao de Filmes", version="0.5.0", docs_url=None)
    app.state.recommender = recommender

    def as_user_read(user) -> UserRead:
        return UserRead(id=user.user_id, name=user.name, preferences=user.preferences)

    def as_movie_read(movie) -> MovieRead:
        return MovieRead(
            id=movie.movie_id,
            title=movie.title,
            tags=movie.tags,
            average_rating=round(movie.average_rating, 3),
            rating_count=movie.rating_count,
        )

    def as_recommendation_read(recommendation) -> RecommendationRead:
        return RecommendationRead(
            movie_id=recommendation.movie.movie_id,
            title=recommendation.movie.title,
            tags=recommendation.movie.tags,
            score=round(recommendation.score, 3),
            source=recommendation.source,
        )

    def as_user_movie_rating_read(entry) -> UserMovieRatingRead:
        return UserMovieRatingRead(
            movie_id=entry.movie.movie_id,
            title=entry.movie.title,
            tags=entry.movie.tags,
            rating=entry.rating,
            average_rating=round(entry.movie.average_rating, 3),
            rating_count=entry.movie.rating_count,
        )

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "message": "Sistema de recomendacao de filmes em FastAPI",
            "domain": "movies",
            "status": "api com persistencia SQLite e recomendador hibrido prontos",
            "dataset": recommender.dataset_source,
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/docs", include_in_schema=False)
    def custom_swagger_ui() -> HTMLResponse:
        response = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
        )
        html = response.body.decode("utf-8").replace(
            "</head>",
            """
    <style>
      .swagger-ui .info .title span,
      .swagger-ui .info a.link {
        display: none !important;
      }
    </style>
    </head>
    """,
        )
        return HTMLResponse(html)

    @app.get("/dataset", response_model=DatasetRead)
    def dataset_info() -> DatasetRead:
        return DatasetRead(
            source=recommender.dataset_source,
            movies=len(recommender.movies),
            registered_users=len(recommender.users),
        )

    @app.post("/users", response_model=UserRead, status_code=201)
    def create_user(payload: UserCreate) -> UserRead:
        user = recommender.create_user(payload.name, payload.preferences)
        return as_user_read(user)

    @app.post("/movies", response_model=MovieRead, status_code=201)
    def create_movie(payload: MovieCreate) -> MovieRead:
        movie = recommender.create_movie(payload.title, payload.tags)
        return as_movie_read(movie)

    @app.get("/movies", response_model=list[MovieRead])
    def list_movies(
        q: str | None = None,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> list[MovieRead]:
        movies = recommender.search_movies(q, limit=limit) if q else recommender.list_movies(limit=limit, offset=offset)
        return [as_movie_read(movie) for movie in movies]

    @app.get("/movies/popular", response_model=list[RecommendationRead])
    def get_popular_movies(limit: int = Query(default=10, ge=1, le=50)) -> list[RecommendationRead]:
        recommendations = recommender.popular_movies(limit=limit)
        return [as_recommendation_read(recommendation) for recommendation in recommendations]

    @app.get("/movies/{movie_id}", response_model=MovieRead)
    def get_movie(movie_id: int) -> MovieRead:
        try:
            movie = recommender.get_movie(movie_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Filme nao encontrado.") from error
        return as_movie_read(movie)

    @app.get("/users/{user_id}/recommendations", response_model=list[RecommendationRead])
    def get_recommendations(user_id: int, limit: int = Query(default=5, ge=1, le=20)) -> list[RecommendationRead]:
        try:
            recommendations = recommender.recommend_for_user(user_id, limit)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Usuario nao encontrado.") from error
        return [as_recommendation_read(recommendation) for recommendation in recommendations]

    @app.get("/users/{user_id}/ratings", response_model=list[UserMovieRatingRead])
    def get_user_ratings(user_id: int) -> list[UserMovieRatingRead]:
        try:
            ratings = recommender.get_user_ratings(user_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Usuario nao encontrado.") from error
        return [as_user_movie_rating_read(entry) for entry in ratings]

    @app.put("/users/{user_id}/preferences", response_model=UserRead)
    def update_preferences(user_id: int, payload: PreferenceUpdate) -> UserRead:
        try:
            user = recommender.update_preferences(user_id, payload.preferences)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Usuario nao encontrado.") from error
        return as_user_read(user)

    @app.post("/users/{user_id}/ratings", response_model=RatingRead, status_code=201)
    def rate_movie(user_id: int, payload: RatingCreate) -> RatingRead:
        try:
            user, _movie = recommender.rate_movie(user_id, payload.movie_id, payload.rating)
        except KeyError as error:
            error_message = str(error.args[0] if error.args else "")
            message = "Usuario nao encontrado." if "User" in error_message else "Filme nao encontrado."
            raise HTTPException(status_code=404, detail=message) from error
        return RatingRead(user_id=user.user_id, movie_id=payload.movie_id, rating=payload.rating)

    return app


app = create_app()
