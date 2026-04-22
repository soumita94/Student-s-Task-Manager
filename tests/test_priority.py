from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Allow `python test_priority.py` from the `tests/` folder (cwd is not the project root).
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pytest

from app.models import TaskKind
from app.services.priority import compute_priority_score


def test_urgency_increases_as_deadline_nears() -> None:
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    far = now + timedelta(days=14)
    soon = now + timedelta(hours=6)
    s_far = compute_priority_score(deadline_at=far, importance=5, kind=TaskKind.flexible, now=now)
    s_soon = compute_priority_score(deadline_at=soon, importance=5, kind=TaskKind.flexible, now=now)
    assert s_soon > s_far


def test_importance_raises_base_score() -> None:
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    d = now + timedelta(days=3)
    low = compute_priority_score(deadline_at=d, importance=2, kind=TaskKind.flexible, now=now)
    high = compute_priority_score(deadline_at=d, importance=10, kind=TaskKind.flexible, now=now)
    assert high > low


def test_rigid_boosts_over_flexible_at_same_deadline() -> None:
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    d = now + timedelta(hours=12)
    flex = compute_priority_score(deadline_at=d, importance=7, kind=TaskKind.flexible, now=now)
    rigid = compute_priority_score(deadline_at=d, importance=7, kind=TaskKind.rigid, now=now)
    assert rigid >= flex


def test_importance_bounds() -> None:
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    d = now + timedelta(days=1)
    with pytest.raises(ValueError):
        compute_priority_score(deadline_at=d, importance=0, kind=TaskKind.flexible, now=now)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
