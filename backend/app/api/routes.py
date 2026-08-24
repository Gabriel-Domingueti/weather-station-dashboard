from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from app.application.use_cases import (
    GetDailySummary,
    GetHistoricalReadings,
    GetLatestReading,
    compute_staleness,
)
from app.config import settings
from app.domain.models import DailySummary, MetricType, WeatherReading, LatestReadingResponse
from app.infrastructure.csv_repository import CSVRepository
from app.infrastructure.thingspeak_client import ThingSpeakClient
from datetime import datetime, timezone

router = APIRouter()


def get_cache(request: Request):
    return request.app.state.data_cache


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/readings/latest", response_model=LatestReadingResponse)
async def get_latest() -> LatestReadingResponse:
    use_case = GetLatestReading(ThingSpeakClient())
    reading = await use_case.execute()
    
    if reading is None:
        return LatestReadingResponse(
            reading=None,
            is_stale=True,
            minutes_since_reading=None
        )
        
    is_stale, minutes = compute_staleness(
        reading.timestamp,
        datetime.now(timezone.utc),
        settings.stale_threshold_minutes
    )
    
    return LatestReadingResponse(
        reading=reading,
        is_stale=is_stale,
        minutes_since_reading=minutes
    )


@router.get("/readings/daily-summary", response_model=list[DailySummary])
async def get_daily_summary(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    cache=Depends(get_cache),
) -> list[DailySummary]:
    use_case = GetDailySummary(cache)
    return await use_case.execute(start, end)


@router.get("/readings/history", response_model=list[WeatherReading])
async def get_history(
    start: date = Query(...),
    end: date = Query(...),
    metric: MetricType | None = Query(default=None),
) -> list[WeatherReading]:
    if (end - start).days > 92:
        raise HTTPException(status_code=400, detail="Intervalo máximo de 92 dias")

    use_case = GetHistoricalReadings(CSVRepository())
    return await use_case.execute(start, end, metric)


@router.post("/refresh")
async def refresh_cache(
    request: Request,
    x_refresh_token: str = Header(default=""),
    cache=Depends(get_cache),
) -> dict:
    """
    Chamado pelo workflow do GitHub Actions logo após commitar novos CSVs,
    para invalidar o cache sem esperar o próximo ciclo do scheduler.
    """
    if x_refresh_token != settings.refresh_token:
        raise HTTPException(status_code=401, detail="Token inválido")

    await cache.refresh()
    return {"status": "cache atualizado", "rows": len(cache.daily_summary)}
