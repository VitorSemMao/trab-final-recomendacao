from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import sqlite3

from .dataset import MovieRecord, dedupe_preserve_order


@dataclass(slots=True)
class StoredUser:
    user_id: int
    name: str
    preferences: list[str]


class SQLiteStorage:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @classmethod
    def from_env(cls) -> "SQLiteStorage":
        return cls(os.getenv("RECOMMENDER_DB_PATH", "data/recommendation.db"))

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    preferences_json TEXT NOT NULL DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS custom_movies (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    tags_json TEXT NOT NULL DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS ratings (
                    user_id INTEGER NOT NULL,
                    movie_id INTEGER NOT NULL,
                    rating REAL NOT NULL,
                    PRIMARY KEY (user_id, movie_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )

    def load_users(self) -> list[StoredUser]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name, preferences_json FROM users ORDER BY id"
            ).fetchall()

        users: list[StoredUser] = []
        for row in rows:
            preferences = dedupe_preserve_order(json.loads(row["preferences_json"]))
            users.append(StoredUser(user_id=row["id"], name=row["name"], preferences=preferences))
        return users

    def load_custom_movies(self) -> list[MovieRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, title, tags_json FROM custom_movies ORDER BY id"
            ).fetchall()

        return [
            MovieRecord(
                movie_id=row["id"],
                title=row["title"],
                tags=dedupe_preserve_order(json.loads(row["tags_json"])),
            )
            for row in rows
        ]

    def load_ratings(self) -> list[tuple[int, int, float]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT user_id, movie_id, rating FROM ratings ORDER BY user_id, movie_id"
            ).fetchall()
        return [(row["user_id"], row["movie_id"], float(row["rating"])) for row in rows]

    def upsert_user(self, user_id: int, name: str, preferences: list[str]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (id, name, preferences_json)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    preferences_json = excluded.preferences_json
                """,
                (user_id, name, json.dumps(preferences)),
            )

    def upsert_custom_movie(self, movie_id: int, title: str, tags: list[str]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO custom_movies (id, title, tags_json)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    tags_json = excluded.tags_json
                """,
                (movie_id, title, json.dumps(tags)),
            )

    def upsert_rating(self, user_id: int, movie_id: int, rating: float) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ratings (user_id, movie_id, rating)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, movie_id) DO UPDATE SET
                    rating = excluded.rating
                """,
                (user_id, movie_id, rating),
            )
