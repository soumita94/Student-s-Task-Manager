from datetime import datetime, timezone
import math

from app.models import TaskKind

# Tunable weights for MVP; later these can be per-user or learned.
URGENCY_WEIGHT = 0.55
IMPORTANCE_WEIGHT = 0.45
# Hours at which urgency reaches ~63% of its asymptotic curve (continuous, no hard cutoff).
URGENCY_TAU_HOURS = 48.0
RIGID_URGENCY_BOOST = 1.12


def _urgency_from_hours(hours_left: float) -> float:
    """Higher when the deadline is sooner (hours_left small)."""
    if hours_left <= 0:
        return 100.0
    return 100.0 * math.exp(-max(hours_left, 1e-9) / URGENCY_TAU_HOURS)


def compute_priority_score(
    *,
    deadline_at: datetime,
    importance: int,
    kind: TaskKind,
    now: datetime | None = None,
) -> float:
    """
    Dynamic priority in [0, 100]: blends deadline-driven urgency with importance (1–10).
    Rigid tasks get a modest urgency boost to reflect less slack.
    """
    if not 1 <= importance <= 10:
        raise ValueError("importance must be between 1 and 10")

    now = now or datetime.now(timezone.utc)
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)

    hours_left = (deadline_at - now).total_seconds() / 3600.0
    urgency = _urgency_from_hours(hours_left)
    if kind == TaskKind.rigid:
        urgency = min(100.0, urgency * RIGID_URGENCY_BOOST)

    importance_norm = (importance / 10.0) * 100.0
    return round(URGENCY_WEIGHT * urgency + IMPORTANCE_WEIGHT * importance_norm, 4)
