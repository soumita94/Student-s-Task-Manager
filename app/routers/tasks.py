from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Task
from app.schemas import NLPQuickAddRequest, SortBy, TaskCreate, TaskRead, TaskUpdate
from app.services.nlp_parser import parse_nlp_command_to_task
from app.services.scheduler import calculate_priority_score

router = APIRouter(prefix="/tasks", tags=["tasks"])
nlp_router = APIRouter(prefix="/nlp", tags=["nlp"])


def _score_for_task(task: Task) -> float:
    return calculate_priority_score(
        deadline_at=task.deadline_at,
        category_weight=task.category_weight,
        user_assigned_importance=task.importance,
        user_initial_estimate=task.estimated_minutes,
        kind=task.kind,
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, session: AsyncSession = Depends(get_session)) -> Task:
    score = calculate_priority_score(
        deadline_at=payload.deadline_at,
        category_weight=payload.category_weight,
        user_assigned_importance=payload.importance,
        user_initial_estimate=payload.estimated_minutes,
        kind=payload.kind,
    )
    task = Task(
        title=payload.title,
        description=payload.description,
        kind=payload.kind,
        deadline_at=payload.deadline_at,
        category_weight=payload.category_weight,
        importance=payload.importance,
        estimated_minutes=payload.estimated_minutes,
        actual_time_taken=payload.actual_time_taken,
        priority_score=score,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    session: AsyncSession = Depends(get_session),
    sort_by: SortBy = Query(default=SortBy.priority),
    include_completed: bool = Query(default=False),
) -> list[Task]:
    stmt = select(Task)
    if not include_completed:
        stmt = stmt.where(Task.is_completed.is_(False))

    if sort_by == SortBy.priority:
        stmt = stmt.order_by(Task.priority_score.desc(), Task.deadline_at.asc())
    elif sort_by == SortBy.deadline:
        stmt = stmt.order_by(Task.deadline_at.asc())
    else:
        stmt = stmt.order_by(Task.created_at.desc())

    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)) -> Task:
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    session: AsyncSession = Depends(get_session),
) -> Task:
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(task, field, value)

    if any(k in data for k in ("deadline_at", "importance", "kind")):
        task.priority_score = _score_for_task(task)

    await session.commit()
    await session.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)) -> None:
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await session.delete(task)
    await session.commit()


@nlp_router.post("/quick-add", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def quick_add_task(payload: NLPQuickAddRequest, session: AsyncSession = Depends(get_session)) -> Task:
    try:
        extracted = parse_nlp_command_to_task(payload.text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to parse NLP command: {exc}",
        ) from exc
    return await create_task(extracted, session)
