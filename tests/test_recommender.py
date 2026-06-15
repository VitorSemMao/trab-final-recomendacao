from fastapi.testclient import TestClient

from app.dataset import MovieRatingRecord, MovieRecord
from app.evaluation import evaluate_recommender_precision_at_k
from app.main import create_app
from app.service import RecommendationService
from app.storage import SQLiteStorage


def build_test_client(catalog: list[MovieRecord] | None = None) -> TestClient:
    service = RecommendationService(
        catalog=catalog
        or [
            MovieRecord(1, "Space Journey", ["Sci-Fi", "Adventure"], 12, 4.8),
            MovieRecord(2, "City Lights", ["Drama", "Romance"], 9, 4.1),
            MovieRecord(3, "Laugh Out Loud", ["Comedy"], 15, 4.5),
        ]
    )
    app = create_app(service)
    return TestClient(app)


def test_create_user_and_recommendations() -> None:
    client = build_test_client()

    user_response = client.post("/users", json={"name": "Vitor", "preferences": ["Sci-Fi"]})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    recommendations_response = client.get(f"/users/{user_id}/recommendations", params={"limit": 2})
    assert recommendations_response.status_code == 200

    recommendations = recommendations_response.json()
    assert recommendations[0]["movie_id"] == 1
    assert recommendations[0]["tags"] == ["Sci-Fi", "Adventure"]


def test_create_movie_endpoint() -> None:
    client = build_test_client()

    response = client.post("/movies", json={"title": "Arrival", "tags": ["Sci-Fi", "Drama"]})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Arrival"
    assert body["tags"] == ["Sci-Fi", "Drama"]
    assert body["average_rating"] == 0.0
    assert body["rating_count"] == 0


def test_update_preferences_changes_profile() -> None:
    client = build_test_client()

    user_response = client.post("/users", json={"name": "Vitor", "preferences": ["Drama"]})
    user_id = user_response.json()["id"]

    update_response = client.put(f"/users/{user_id}/preferences", json={"preferences": ["Comedy"]})
    assert update_response.status_code == 200
    assert update_response.json()["preferences"] == ["Comedy"]


def test_ratings_influence_hybrid_recommendations() -> None:
    client = build_test_client(
        catalog=[
            MovieRecord(1, "Shared Anchor", ["Drama"], 20, 4.0),
            MovieRecord(2, "Manual Skip", ["Drama"], 20, 4.0),
            MovieRecord(3, "Future Signal", ["Sci-Fi"], 20, 3.5),
            MovieRecord(4, "Quiet Ending", ["Drama"], 20, 4.0),
        ]
    )

    first_user = client.post("/users", json={"name": "Ana", "preferences": []}).json()["id"]
    second_user = client.post("/users", json={"name": "Bia", "preferences": []}).json()["id"]

    assert client.post(f"/users/{first_user}/ratings", json={"movie_id": 1, "rating": 5}).status_code == 201
    assert client.post(f"/users/{first_user}/ratings", json={"movie_id": 2, "rating": 1}).status_code == 201
    assert client.post(f"/users/{second_user}/ratings", json={"movie_id": 1, "rating": 5}).status_code == 201
    assert client.post(f"/users/{second_user}/ratings", json={"movie_id": 3, "rating": 5}).status_code == 201
    assert client.post(f"/users/{second_user}/ratings", json={"movie_id": 4, "rating": 1}).status_code == 201

    recommendations_response = client.get(f"/users/{first_user}/recommendations", params={"limit": 3})
    assert recommendations_response.status_code == 200

    recommendations = recommendations_response.json()
    assert [entry["movie_id"] for entry in recommendations[:2]] == [3, 4]


def test_list_search_and_popular_movie_endpoints() -> None:
    client = build_test_client()

    list_response = client.get("/movies", params={"limit": 2})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2

    search_response = client.get("/movies", params={"q": "journey"})
    assert search_response.status_code == 200
    search_body = search_response.json()
    assert search_body[0]["title"] == "Space Journey"

    popular_response = client.get("/movies/popular", params={"limit": 2})
    assert popular_response.status_code == 200
    popular_body = popular_response.json()
    assert [entry["movie_id"] for entry in popular_body] == [1, 3]
    assert all(entry["source"] == "popular" for entry in popular_body)


def test_get_movie_and_user_ratings_endpoints() -> None:
    client = build_test_client()

    user_id = client.post("/users", json={"name": "Vitor", "preferences": []}).json()["id"]
    assert client.post(f"/users/{user_id}/ratings", json={"movie_id": 2, "rating": 4}).status_code == 201
    assert client.post(f"/users/{user_id}/ratings", json={"movie_id": 1, "rating": 5}).status_code == 201

    movie_response = client.get("/movies/1")
    assert movie_response.status_code == 200
    assert movie_response.json()["title"] == "Space Journey"

    ratings_response = client.get(f"/users/{user_id}/ratings")
    assert ratings_response.status_code == 200
    ratings_body = ratings_response.json()
    assert [entry["movie_id"] for entry in ratings_body] == [1, 2]
    assert ratings_body[0]["rating"] == 5


def test_cold_start_recommendations_fall_back_to_popular_movies() -> None:
    client = build_test_client()

    user_id = client.post("/users", json={"name": "Novo Usuario", "preferences": []}).json()["id"]
    response = client.get(f"/users/{user_id}/recommendations", params={"limit": 2})

    assert response.status_code == 200
    body = response.json()
    assert [entry["movie_id"] for entry in body] == [1, 3]
    assert all(entry["source"] == "popular" for entry in body)


def test_error_paths_and_validation() -> None:
    client = build_test_client()

    missing_user_response = client.get("/users/999/recommendations")
    assert missing_user_response.status_code == 404
    assert missing_user_response.json()["detail"] == "Usuario nao encontrado."

    missing_movie_response = client.post("/users/1/ratings", json={"movie_id": 999, "rating": 5})
    assert missing_movie_response.status_code == 404
    assert missing_movie_response.json()["detail"] == "Usuario nao encontrado."

    created_user_id = client.post("/users", json={"name": "Ana", "preferences": []}).json()["id"]
    missing_movie_with_valid_user = client.post(
        f"/users/{created_user_id}/ratings",
        json={"movie_id": 999, "rating": 5},
    )
    assert missing_movie_with_valid_user.status_code == 404
    assert missing_movie_with_valid_user.json()["detail"] == "Filme nao encontrado."

    invalid_rating_response = client.post(
        f"/users/{created_user_id}/ratings",
        json={"movie_id": 1, "rating": 6},
    )
    assert invalid_rating_response.status_code == 422

    missing_movie_details = client.get("/movies/999")
    assert missing_movie_details.status_code == 404
    assert missing_movie_details.json()["detail"] == "Filme nao encontrado."

    missing_user_ratings = client.get("/users/999/ratings")
    assert missing_user_ratings.status_code == 404
    assert missing_user_ratings.json()["detail"] == "Usuario nao encontrado."


def test_sqlite_persistence_restores_users_movies_and_ratings(tmp_path) -> None:
    database_path = tmp_path / "recommender.db"
    storage = SQLiteStorage(database_path)
    catalog = [
        MovieRecord(1, "Space Journey", ["Sci-Fi", "Adventure"], 12, 4.8),
        MovieRecord(2, "City Lights", ["Drama", "Romance"], 9, 4.1),
    ]

    first_service = RecommendationService(catalog=catalog, storage=storage)
    user = first_service.create_user("Ana", ["Sci-Fi"])
    custom_movie = first_service.create_movie("Arrival", ["Sci-Fi", "Drama"])
    first_service.rate_movie(user.user_id, 1, 5)
    first_service.rate_movie(user.user_id, custom_movie.movie_id, 4)
    first_service.update_preferences(user.user_id, ["Drama", "Sci-Fi"])

    restored_service = RecommendationService(catalog=catalog, storage=SQLiteStorage(database_path))

    restored_user = restored_service.users[user.user_id]
    assert restored_user.name == "Ana"
    assert restored_user.preferences == ["Drama", "Sci-Fi"]
    assert restored_user.ratings == {1: 5.0, custom_movie.movie_id: 4.0}

    restored_movie = restored_service.movies[custom_movie.movie_id]
    assert restored_movie.title == "Arrival"
    assert restored_movie.tags == ["Sci-Fi", "Drama"]

    base_movie = restored_service.movies[1]
    assert base_movie.rating_count == 13
    assert round(base_movie.average_rating, 3) == round((12 * 4.8 + 5) / 13, 3)


def test_evaluation_metric_returns_consistent_result_shape() -> None:
    catalog = [
        MovieRecord(1, "Shared One", ["Drama"], 10, 4.6),
        MovieRecord(2, "Shared Two", ["Drama"], 10, 4.5),
        MovieRecord(3, "Sci-Fi Signal", ["Sci-Fi"], 10, 4.7),
        MovieRecord(4, "Romance Beat", ["Romance"], 10, 4.2),
    ]
    rating_history = {
        1: [
            MovieRatingRecord(1, 1, 5, 1),
            MovieRatingRecord(1, 2, 4, 2),
            MovieRatingRecord(1, 3, 5, 3),
            MovieRatingRecord(1, 4, 2, 4),
            MovieRatingRecord(1, 2, 5, 5),
        ],
        2: [
            MovieRatingRecord(2, 1, 5, 1),
            MovieRatingRecord(2, 3, 5, 2),
            MovieRatingRecord(2, 2, 4, 3),
            MovieRatingRecord(2, 4, 1, 4),
            MovieRatingRecord(2, 3, 5, 5),
        ],
    }

    result = evaluate_recommender_precision_at_k(
        catalog=catalog,
        dataset_source="synthetic",
        rating_history=rating_history,
        k=2,
        min_ratings_per_user=5,
        positive_threshold=4.0,
        max_users=10,
    )

    assert result.dataset_source == "synthetic"
    assert result.users_evaluated == 2
    assert 0.0 <= result.precision_at_k <= 1.0
    assert 0.0 <= result.hit_rate_at_k <= 1.0
