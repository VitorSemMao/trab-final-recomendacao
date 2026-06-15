from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.dataset import load_movie_catalog, load_movielens_rating_history
from app.evaluation import evaluate_recommender_precision_at_k


def main() -> None:
    catalog, catalog_source = load_movie_catalog()
    rating_history, ratings_source = load_movielens_rating_history()
    result = evaluate_recommender_precision_at_k(
        catalog=catalog,
        dataset_source=catalog_source,
        rating_history=rating_history,
        k=5,
        min_ratings_per_user=5,
        positive_threshold=4.0,
        max_users=200,
    )
    print(
        json.dumps(
            {
                "dataset_catalog": result.dataset_source,
                "ratings_source": ratings_source,
                "users_evaluated": result.users_evaluated,
                "k": result.k,
                "positive_threshold": result.positive_threshold,
                "hits_at_k": result.hits_at_k,
                "precision_at_k": round(result.precision_at_k, 4),
                "hit_rate_at_k": round(result.hit_rate_at_k, 4),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
