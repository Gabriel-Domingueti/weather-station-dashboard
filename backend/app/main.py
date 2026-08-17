import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.core.cache import data_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.data_cache = data_cache
    try:
        await data_cache.refresh()
    except Exception as e:
        logger.warning("Não foi possível carregar o cache inicial no startup (%s). O backend continuará rodando.", e)

    scheduler.add_job(
        data_cache.refresh,
        "interval",
        minutes=settings.cache_refresh_minutes,
        id="refresh_data_cache",
    )
    scheduler.start()
    logger.info("Scheduler iniciado (refresh a cada %s min)", settings.cache_refresh_minutes)

    yield

    scheduler.shutdown()


app = FastAPI(title="Weather Station Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
