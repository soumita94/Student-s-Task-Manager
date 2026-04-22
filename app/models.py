import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TaskKind(str, enum.Enum):
    """Rigid tasks have hard deadlines; flexible tasks can be spread."""

    rigid = "rigid"
    flexible = "flexible"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[TaskKind] = mapped_column(
        Enum(TaskKind, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TaskKind.flexible,
    )
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    category_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=5)  # 1–10 academic/career weight
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_time_taken: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
