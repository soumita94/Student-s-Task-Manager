from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.linear_model import LinearRegression
from sqlalchemy import create_engine, text

from app.config import settings

MODEL_PATH = Path(__file__).resolve().parent / "duration_model.joblib"


def _sync_database_url(async_url: str) -> str:
    return async_url.replace("+aiosqlite", "")


def train_model(model_path: Path | None = None, min_rows: int = 8) -> Path:
    """
    Train a linear regression model from historical task records and save it.
    Features: (category_weight, user_assigned_importance, user_initial_estimate)
    Target: actual_time_taken
    """
    output_path = model_path or MODEL_PATH
    engine = create_engine(_sync_database_url(settings.database_url))

    query = text(
        """
        SELECT
            category_weight,
            importance AS user_assigned_importance,
            estimated_minutes AS user_initial_estimate,
            actual_time_taken
        FROM tasks
        WHERE actual_time_taken IS NOT NULL
          AND estimated_minutes IS NOT NULL
          AND category_weight IS NOT NULL
          AND importance IS NOT NULL
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()

    if len(rows) < min_rows:
        raise ValueError(
            f"Not enough historical samples to train model. "
            f"Need at least {min_rows}, found {len(rows)}."
        )

    X = [
        [
            float(r["category_weight"]),
            float(r["user_assigned_importance"]),
            float(r["user_initial_estimate"]),
        ]
        for r in rows
    ]
    y = [float(r["actual_time_taken"]) for r in rows]

    model = LinearRegression()
    model.fit(X, y)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    return output_path


def predict_duration_minutes(
    *,
    category_weight: float,
    user_assigned_importance: int,
    user_initial_estimate: int | None,
    model_path: Path | None = None,
) -> float:
    """
    Predict task duration in minutes.
    Falls back to user estimate when model is unavailable.
    """
    initial_estimate = float(user_initial_estimate or 60)
    path = model_path or MODEL_PATH
    if not path.exists():
        return initial_estimate

    model = joblib.load(path)
    prediction = model.predict(
        [[float(category_weight), float(user_assigned_importance), initial_estimate]]
    )[0]
    return max(1.0, float(prediction))

