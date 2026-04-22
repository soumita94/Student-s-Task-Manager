from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import tasks

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Student Task & Schedule Manager",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(tasks.router)
app.include_router(tasks.nlp_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
