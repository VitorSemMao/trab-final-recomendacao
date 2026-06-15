from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, replace
from math import sqrt

from .dataset import MovieRecord, dedupe_preserve_order, load_movie_catalog, normalize_text
from .storage import SQLiteStorage


TAG_ALIASES = {
    "acao": "action",
    "action": "action",
    "aventura": "adventure",
    "adventure": "adventure",
    "animacao": "animation",
    "animation": "animation",
    "criancas": "children's",
    "children's": "children's",
    "comedia": "comedy",
    "comedy": "comedy",
    "crime": "crime",
    "documentario": "documentary",
    "documentary": "documentary",
    "drama": "drama",
    "fantasia": "fantasy",
    "fantasy": "fantasy",
    "film noir": "film-noir",
    "terror": "horror",
    "horror": "horror",
    "musical": "musical",
    "misterio": "mystery",
    "mystery": "mystery",
    "romance": "romance",
    "ficcao cientifica": "sci-fi",
    "science fiction": "sci-fi",
    "sci fi": "sci-fi",
    "sci-fi": "sci-fi",
    "suspense": "thriller",
    "thriller": "thriller",
    "guerra": "war",
    "war": "war",
    "western": "western",
}

CUSTOM_MOVIE_ID_START = 100_000


@dataclass(slots=True)
class UserRecord:
    user_id: int
    name: str
    preferences: list[str] = field(default_factory=list)
    ratings: dict[int, float] = field(default_factory=dict)


@dataclass(slots=True)
class RecommendationResult:
    movie: MovieRecord
    score: float
    source: str = "hybrid"


@dataclass(slots=True)
class UserMovieRating:
    movie: MovieRecord
    rating: float


class RecommendationService:
    def __init__(self, catalog: list[MovieRecord] | None = None, storage: SQLiteStorage | None = None) -> None:
        self.storage = storage if storage is not None else (SQLiteStorage.from_env() if catalog is None else None)

        if catalog is None:
            loaded_catalog, dataset_source = load_movie_catalog()
        else:
            loaded_catalog = [replace(movie, tags=list(movie.tags)) for movie in catalog]
            dataset_source = "custom catalog"

        self.movies: dict[int, MovieRecord] = {movie.movie_id: movie for movie in loaded_catalog}
        self.dataset_source = dataset_source

        if self.storage is not None:
            for movie in self.storage.load_custom_movies():
                self.movies[movie.movie_id] = movie

        self.users: dict[int, UserRecord] = {}
        if self.storage is not None:
            for stored_user in self.storage.load_users():
                self.users[stored_user.user_id] = UserRecord(
                    user_id=stored_user.user_id,
                    name=stored_user.name,
                    preferences=stored_user.preferences,
                )
            for user_id, movie_id, rating in self.storage.load_ratings():
                user = self.users.get(user_id)
                movie = self.movies.get(movie_id)
                if user is None or movie is None:
                    continue
                self._apply_rating(user, movie, rating)

        self.next_user_id = max(self.users, default=0) + 1
        self.next_movie_id = max(max(self.movies, default=0) + 1, CUSTOM_MOVIE_ID_START)

    def create_user(self, name: str, preferences: list[str] | None = None) -> UserRecord:
        cleaned_preferences = dedupe_preserve_order(preferences or [])
        user = UserRecord(user_id=self.next_user_id, name=name.strip(), preferences=cleaned_preferences)
        self.users[user.user_id] = user
        self.next_user_id += 1
        if self.storage is not None:
            self.storage.upsert_user(user.user_id, user.name, user.preferences)
        return user

    def create_movie(self, title: str, tags: list[str] | None = None) -> MovieRecord:
        cleaned_tags = dedupe_preserve_order(tags or [])
        movie = MovieRecord(movie_id=self.next_movie_id, title=title.strip(), tags=cleaned_tags)
        self.movies[movie.movie_id] = movie
        self.next_movie_id += 1
        if self.storage is not None:
            self.storage.upsert_custom_movie(movie.movie_id, movie.title, movie.tags)
        return movie

    def list_movies(self, *, limit: int = 20, offset: int = 0) -> list[MovieRecord]:
        ordered_movies = sorted(
            self.movies.values(),
            key=lambda movie: (
                normalize_text(movie.title),
                movie.movie_id,
            ),
        )
        return ordered_movies[offset : offset + limit]

    def search_movies(self, query: str, *, limit: int = 20) -> list[MovieRecord]:
        normalized_query = normalize_text(query)
        if not normalized_query:
            return self.list_movies(limit=limit, offset=0)

        matches = [
            movie
            for movie in self.movies.values()
            if normalized_query in normalize_text(movie.title)
            or any(normalized_query in normalize_text(tag) for tag in movie.tags)
        ]
        matches.sort(
            key=lambda movie: (
                normalized_query not in normalize_text(movie.title),
                normalize_text(movie.title),
                movie.movie_id,
            ),
        )
        return matches[:limit]

    def update_preferences(self, user_id: int, preferences: list[str]) -> UserRecord:
        user = self._get_user(user_id)
        user.preferences = dedupe_preserve_order(preferences)
        if self.storage is not None:
            self.storage.upsert_user(user.user_id, user.name, user.preferences)
        return user

    def get_movie(self, movie_id: int) -> MovieRecord:
        return self._get_movie(movie_id)

    def get_user_ratings(self, user_id: int) -> list[UserMovieRating]:
        user = self._get_user(user_id)
        ratings = [
            UserMovieRating(movie=self._get_movie(movie_id), rating=rating)
            for movie_id, rating in user.ratings.items()
            if movie_id in self.movies
        ]
        ratings.sort(
            key=lambda entry: (
                -entry.rating,
                normalize_text(entry.movie.title),
                entry.movie.movie_id,
            ),
        )
        return ratings

    def popular_movies(self, *, limit: int = 10, exclude_movie_ids: set[int] | None = None) -> list[RecommendationResult]:
        hidden_movie_ids = exclude_movie_ids or set()
        recommendations = [
            RecommendationResult(
                movie=movie,
                score=self._popularity_score(movie),
                source="popular",
            )
            for movie in self.movies.values()
            if movie.movie_id not in hidden_movie_ids
        ]
        recommendations.sort(
            key=lambda result: (
                -result.score,
                normalize_text(result.movie.title),
                result.movie.movie_id,
            )
        )
        return recommendations[:limit]

    def rate_movie(self, user_id: int, movie_id: int, rating: float) -> tuple[UserRecord, MovieRecord]:
        user = self._get_user(user_id)
        movie = self._get_movie(movie_id)
        self._apply_rating(user, movie, rating)
        if self.storage is not None:
            self.storage.upsert_rating(user.user_id, movie.movie_id, rating)
        return user, movie

    def _apply_rating(self, user: UserRecord, movie: MovieRecord, rating: float) -> None:
        previous_rating = user.ratings.get(movie.movie_id)
        if previous_rating is None:
            movie.rating_count += 1
            movie.rating_total += rating
        else:
            movie.rating_total += rating - previous_rating

        movie.average_rating = movie.rating_total / movie.rating_count if movie.rating_count else 0.0
        user.ratings[movie.movie_id] = rating

    def recommend_for_user(self, user_id: int, limit: int = 5) -> list[RecommendationResult]:
        user = self._get_user(user_id)
        if not user.preferences and not user.ratings:
            return self.popular_movies(limit=limit)

        profile_weights = self._build_profile_weights(user)

        recommendations: list[RecommendationResult] = []
        for movie in self.movies.values():
            if movie.movie_id in user.ratings:
                continue
            content_score = self._content_score(movie, profile_weights)
            collaborative_score = self._collaborative_score(user, movie.movie_id)
            score = (content_score * 0.7) + (collaborative_score * 0.3)
            recommendations.append(RecommendationResult(movie=movie, score=score, source="hybrid"))

        recommendations.sort(
            key=lambda result: (
                -result.score,
                normalize_text(result.movie.title),
                result.movie.movie_id,
            )
        )
        return recommendations[:limit]

    def _get_user(self, user_id: int) -> UserRecord:
        user = self.users.get(user_id)
        if user is None:
            raise KeyError(f"User {user_id} not found")
        return user

    def _get_movie(self, movie_id: int) -> MovieRecord:
        movie = self.movies.get(movie_id)
        if movie is None:
            raise KeyError(f"Movie {movie_id} not found")
        return movie

    def _build_profile_weights(self, user: UserRecord) -> Counter[str]:
        weights: Counter[str] = Counter()
        for preference in user.preferences:
            normalized_preference = normalize_text(preference)
            if not normalized_preference:
                continue
            canonical_preference = TAG_ALIASES.get(normalized_preference, normalized_preference)
            weights[canonical_preference] += 2.0 if canonical_preference != normalized_preference else 1.0

        for movie_id, rating in user.ratings.items():
            movie = self.movies.get(movie_id)
            if movie is None:
                continue
            signal = rating - 3.0
            if signal == 0:
                continue
            for tag in movie.tags:
                normalized_tag = normalize_text(tag)
                canonical_tag = TAG_ALIASES.get(normalized_tag, normalized_tag)
                weights[canonical_tag] += signal
        return weights

    def _content_score(self, movie: MovieRecord, profile_weights: Counter[str]) -> float:
        normalized_movie_tags = {normalize_text(tag) for tag in movie.tags}
        normalized_title = normalize_text(movie.title)

        score = (movie.average_rating / 5.0) * 2.5
        score += min(movie.rating_count, 1000) / 1000.0

        for preference, weight in profile_weights.items():
            if preference in normalized_movie_tags:
                score += 1.8 * weight
            elif preference in normalized_title:
                score += 0.4 * weight

        return score

    def _popularity_score(self, movie: MovieRecord) -> float:
        rated_movies = [entry for entry in self.movies.values() if entry.rating_count > 0]
        if not rated_movies:
            return 0.0

        global_average = sum(entry.average_rating for entry in rated_movies) / len(rated_movies)
        minimum_votes = 50
        vote_count = movie.rating_count
        return ((vote_count * movie.average_rating) + (minimum_votes * global_average)) / (vote_count + minimum_votes)

    def _collaborative_score(self, target_user: UserRecord, movie_id: int) -> float:
        weighted_total = 0.0
        similarity_total = 0.0

        for other_user in self.users.values():
            if other_user.user_id == target_user.user_id:
                continue

            rating = other_user.ratings.get(movie_id)
            if rating is None:
                continue

            similarity = self._user_similarity(target_user, other_user)
            if similarity <= 0:
                continue

            weighted_total += similarity * rating
            similarity_total += similarity

        if similarity_total <= 0:
            return 0.0

        return weighted_total / similarity_total

    def _user_similarity(self, left_user: UserRecord, right_user: UserRecord) -> float:
        common_movie_ids = set(left_user.ratings).intersection(right_user.ratings)
        if not common_movie_ids:
            return 0.0

        left_vector: list[float] = []
        right_vector: list[float] = []
        for movie_id in common_movie_ids:
            left_vector.append(left_user.ratings[movie_id] - 3.0)
            right_vector.append(right_user.ratings[movie_id] - 3.0)

        left_norm = sqrt(sum(value * value for value in left_vector))
        right_norm = sqrt(sum(value * value for value in right_vector))
        if left_norm == 0 or right_norm == 0:
            return 0.0

        numerator = sum(left_value * right_value for left_value, right_value in zip(left_vector, right_vector))
        return numerator / (left_norm * right_norm)
