import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pr_review_shared.config import settings
from pr_review_shared.db import init_db
from pr_review_shared.logging import configure_logging

from .routers import repos, reviews, stats

configure_logging("api", settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI-Powered PR Review Assistant - Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


app.include_router(reviews.router)
app.include_router(repos.router)
app.include_router(stats.router)
