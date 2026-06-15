from fastapi.testclient import TestClient

from app.dataset import MovieRecord
from app.main import create_app
from app.service import RecommendationService


client = TestClient(
    create_app(
        RecommendationService(
            catalog=[
                MovieRecord(1, "Space Journey", ["Sci-Fi", "Adventure"], 12, 4.8),
                MovieRecord(2, "City Lights", ["Drama", "Romance"], 9, 4.1),
            ]
        )
    )
)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["domain"] == "movies"
    assert body["status"] == "api com persistencia SQLite e recomendador hibrido prontos"
