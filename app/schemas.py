from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TaskKind


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    kind: TaskKind = TaskKind.flexible
    deadline_at: datetime
    category_weight: float = Field(ge=0.1, le=10.0, default=1.0)
    importance: int = Field(ge=1, le=10, default=5)
    estimated_minutes: int | None = Field(default=None, ge=1)
    actual_time_taken: int | None = Field(default=None, ge=1)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    kind: TaskKind | None = None
    deadline_at: datetime | None = None
    category_weight: float | None = Field(default=None, ge=0.1, le=10.0)
    importance: int | None = Field(default=None, ge=1, le=10)
    estimated_minutes: int | None = Field(default=None, ge=1)
    actual_time_taken: int | None = Field(default=None, ge=1)
    is_completed: bool | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_completed: bool
    priority_score: float
    created_at: datetime
    updated_at: datetime


class SortBy(str, Enum):
    priority = "priority"
    deadline = "deadline"
    created = "created"


class NLPQuickAddRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
