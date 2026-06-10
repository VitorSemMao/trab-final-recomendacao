from fastapi.testclient import TestClient

from app.dataset import MovieRecord
from app.main import create_app
from app.service import RecommendationService


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
