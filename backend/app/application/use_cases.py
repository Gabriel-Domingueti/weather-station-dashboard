from datetime import date

import pandas as pd

from app.core.cache import DataCache
from app.domain.models import DailySummary, MetricType, WeatherReading
from app.infrastructure.csv_repository import CSVRepository
from app.infrastructure.thingspeak_client import ThingSpeakClient


def compute_staleness(reading_timestamp, now, threshold_minutes: int) -> tuple[bool, float]:
    """Retorna (esta_desatualizado, minutos_desde_a_leitura)."""
    delta = now - reading_timestamp
    minutes = delta.total_seconds() / 60.0
    is_stale = minutes >= threshold_minutes
    return is_stale, minutes


class GetLatestReading:
    """Use case: retorna a condição atual, direto do ThingSpeak."""

    def __init__(self, thingspeak_client: ThingSpeakClient) -> None:
        self._thingspeak_client = thingspeak_client

    async def execute(self) -> WeatherReading | None:
        return await self._thingspeak_client.get_latest()


class GetDailySummary:
    """Use case: retorna o resumo diário (histórico agregado), do cache."""

    def __init__(self, cache: DataCache) -> None:
        self._cache = cache

    async def execute(self, start: date | None, end: date | None) -> list[DailySummary]:
        await self._cache.ensure_fresh()
        df = self._cache.daily_summary

        if df.empty:
            return []

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        if start:
            df = df[df["date"] >= start]
        if end:
            df = df[df["date"] <= end]

        df["date"] = df["date"].astype(str)

        # mesmo motivo do GetHistoricalReadings: NaN não é JSON válido
        df = df.astype(object).where(pd.notnull(df), None)

        return [DailySummary(**row) for row in df.to_dict(orient="records")]


class GetHistoricalReadings:
    """Use case: retorna leituras brutas (não agregadas) de um período/métrica."""

    def __init__(self, repository: CSVRepository) -> None:
        self._repository = repository

    async def execute(
        self, start: date, end: date, metric: MetricType | None = None
    ) -> list[WeatherReading]:
        df = await self._repository.fetch_raw_range(start, end)
        if df.empty:
            return []

        if metric:
            columns = ["timestamp", metric.value]
            df = df[columns]

        # pandas mantém ausências como NaN (float), e o Pydantic aceita NaN
        # como float válido silenciosamente — sem essa conversão, o contrato
        # "float | None" do WeatherReading vira NaN em vez de None.
        df = df.astype(object).where(pd.notnull(df), None)

        return [WeatherReading(**row) for row in df.to_dict(orient="records")]