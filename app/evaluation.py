from __future__ import annotations

from dataclasses import dataclass

from .dataset import MovieRatingRecord, MovieRecord
from .service import RecommendationService


@dataclass(slots=True)
class EvaluationResult:
    dataset_source: str
    users_evaluated: int
    hits_at_k: int
    precision_at_k: float
    hit_rate_at_k: float
    k: int
    positive_threshold: float


def evaluate_recommender_precision_at_k(
    *,
    catalog: list[MovieRecord],
    dataset_source: str,
    rating_history: dict[int, list[MovieRatingRecord]],
    k: int = 5,
    min_ratings_per_user: int = 5,
    positive_threshold: float = 4.0,
    max_users: int = 200,
) -> EvaluationResult:
    service = RecommendationService(catalog=catalog)
    evaluation_pairs: list[tuple[int, MovieRatingRecord]] = []

    for real_user_id, ratings in sorted(rating_history.items()):
        if len(ratings) < min_ratings_per_user:
            continue

        positive_ratings = [entry for entry in ratings if entry.rating >= positive_threshold]
        if len(positive_ratings) < 2:
            continue

        holdout = positive_ratings[-1]
        training_ratings = [
            entry
            for entry in ratings
            if not (entry.movie_id == holdout.movie_id and entry.timestamp == holdout.timestamp)
        ]
        if len(training_ratings) < min_ratings_per_user - 1:
            continue

        service_user = service.create_user(f"eval_user_{real_user_id}", [])
        applied_training_ratings = 0
        for entry in training_ratings:
            if entry.movie_id not in service.movies:
                continue
            service.rate_movie(service_user.user_id, entry.movie_id, entry.rating)
            applied_training_ratings += 1

        if applied_training_ratings < min_ratings_per_user - 1:
            del service.users[service_user.user_id]
            continue

        evaluation_pairs.append((service_user.user_id, holdout))
        if len(evaluation_pairs) >= max_users:
            break

    if not evaluation_pairs:
        return EvaluationResult(
            dataset_source=dataset_source,
            users_evaluated=0,
            hits_at_k=0,
            precision_at_k=0.0,
            hit_rate_at_k=0.0,
            k=k,
            positive_threshold=positive_threshold,
        )

    hits_at_k = 0
    for service_user_id, holdout in evaluation_pairs:
        recommended_movie_ids = {
            recommendation.movie.movie_id
            for recommendation in service.recommend_for_user(service_user_id, limit=k)
        }
        if holdout.movie_id in recommended_movie_ids:
            hits_at_k += 1

    users_evaluated = len(evaluation_pairs)
    return EvaluationResult(
        dataset_source=dataset_source,
        users_evaluated=users_evaluated,
        hits_at_k=hits_at_k,
        precision_at_k=hits_at_k / (users_evaluated * k),
        hit_rate_at_k=hits_at_k / users_evaluated,
        k=k,
        positive_threshold=positive_threshold,
    )
