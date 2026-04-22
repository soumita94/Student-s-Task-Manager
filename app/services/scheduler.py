from __future__ import annotations

from datetime import datetime, timezone
import math

from app.analytics.duration_model import predict_duration_minutes
from app.models import TaskKind

# Tunable weights for MVP; now includes duration-aware urgency shaping.
URGENCY_WEIGHT = 0.55
IMPORTANCE_WEIGHT = 0.45
URGENCY_TAU_HOURS = 48.0
RIGID_URGENCY_BOOST = 1.12
PREDICTED_DURATION_PRESSURE = 0.7


def _urgency_from_hours(hours_left: float) -> float:
    if hours_left <= 0:
        return 100.0
    return 100.0 * math.exp(-max(hours_left, 1e-9) / URGENCY_TAU_HOURS)


def calculate_priority_score(
    *,
    deadline_at: datetime,
    category_weight: float,
    user_assigned_importance: int,
    user_initial_estimate: int | None,
    kind: TaskKind,
    now: datetime | None = None,
) -> float:
    """
    Duration-aware dynamic priority:
    - Predicts duration from behavioral model
    - Tightens effective time-to-deadline for long tasks
    - Blends urgency and importance
    """
    if not 1 <= user_assigned_importance <= 10:
        raise ValueError("user_assigned_importance must be between 1 and 10")

    now = now or datetime.now(timezone.utc)
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)

    predicted_minutes = predict_duration_minutes(
        category_weight=category_weight,
        user_assigned_importance=user_assigned_importance,
        user_initial_estimate=user_initial_estimate,
    )
    predicted_hours = predicted_minutes / 60.0

    hours_left = (deadline_at - now).total_seconds() / 3600.0
    effective_hours_left = hours_left - (predicted_hours * PREDICTED_DURATION_PRESSURE)

    urgency = _urgency_from_hours(effective_hours_left)
    if kind == TaskKind.rigid:
        urgency = min(100.0, urgency * RIGID_URGENCY_BOOST)

    importance_norm = (user_assigned_importance / 10.0) * 100.0
    return round(URGENCY_WEIGHT * urgency + IMPORTANCE_WEIGHT * importance_norm, 4)

