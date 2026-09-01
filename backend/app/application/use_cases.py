from datetime import date

import pandas as pd

from app.core.cache import DataCache
from app.domain.models import DailySummary, MetricType, WeatherReading, MonthlyRecords, MetricRecord, TrendInfo, AgroIndex
from app.infrastructure.csv_repository import CSVRepository
from datetime import datetime, timezone, timedelta
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


def compute_trend(current: float, reference: float, threshold: float = 0.5) -> str:
    """Retorna 'rising', 'falling' ou 'stable'."""
    diff = current - reference
    if abs(diff) <= threshold:
        return "stable"
    if diff > 0:
        return "rising"
    return "falling"


def compute_rain_alert(pressure_change_hpa: float, threshold_hpa: float = 3.5) -> bool:
    """
    True se a pressão caiu mais que threshold_hpa no período de
    referência. Só dispara em queda (valor negativo), nunca em subida.
    """
    if pressure_change_hpa > 0:
        return False
    return abs(pressure_change_hpa) >= threshold_hpa


class GetMonthlyRecords:
    def __init__(self, cache: DataCache) -> None:
        self._cache = cache

    async def execute(self, year: int, month: int) -> MonthlyRecords:
        await self._cache.ensure_fresh()
        df = self._cache.daily_summary
        
        month_str = f"{year:04d}-{month:02d}"
        
        empty_record = MetricRecord(max_value=None, max_date=None, min_value=None, min_date=None)
        if df.empty:
            return MonthlyRecords(month=month_str, temperature=empty_record, humidity=empty_record, pressure=empty_record)
            
        df = df.copy()
        # Filtrar o mês
        df["date_str"] = df["date"].astype(str)
        df_month = df[df["date_str"].str.startswith(month_str)]
        
        if df_month.empty:
            return MonthlyRecords(month=month_str, temperature=empty_record, humidity=empty_record, pressure=empty_record)
            
        def get_metric_record(metric_prefix: str) -> MetricRecord:
            max_col = f"{metric_prefix}_max"
            min_col = f"{metric_prefix}_min"
            
            # max
            valid_max = df_month[pd.notnull(df_month[max_col])]
            if valid_max.empty:
                max_val = None
                max_date = None
            else:
                max_idx = valid_max[max_col].idxmax()
                max_val = valid_max.loc[max_idx, max_col]
                max_date = valid_max.loc[max_idx, "date_str"]
                
            # min
            valid_min = df_month[pd.notnull(df_month[min_col])]
            if valid_min.empty:
                min_val = None
                min_date = None
            else:
                min_idx = valid_min[min_col].idxmin()
                min_val = valid_min.loc[min_idx, min_col]
                min_date = valid_min.loc[min_idx, "date_str"]
                
            return MetricRecord(
                max_value=max_val, max_date=max_date,
                min_value=min_val, min_date=min_date
            )
            
        return MonthlyRecords(
            month=month_str,
            temperature=get_metric_record("temperature"),
            humidity=get_metric_record("humidity"),
            pressure=get_metric_record("pressure"),
        )


class GetTrend:
    def __init__(self, thingspeak_client: ThingSpeakClient, repository: CSVRepository) -> None:
        self._thingspeak = thingspeak_client
        self._repository = repository
        
    async def execute(self) -> TrendInfo:
        current = await self._thingspeak.get_latest()
        
        default_trend = TrendInfo(temperature="stable", humidity="stable", pressure="stable")
        if not current:
            return default_trend
            
        now = datetime.now(timezone.utc)
        ref_time_end = now - timedelta(hours=2, minutes=30)
        ref_time_start = now - timedelta(hours=3, minutes=30)
        
        df = await self._repository.fetch_raw_range(ref_time_start.date(), ref_time_end.date())
        if df.empty:
            return default_trend
            
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        # Filtrar o intervalo
        df_ref = df[(df["timestamp"] >= ref_time_start) & (df["timestamp"] <= ref_time_end)]
        if df_ref.empty:
            return default_trend
            
        # Pegar a linha mais próxima do centro (3 hours ago)
        target_time = now - timedelta(hours=3)
        df_ref = df_ref.copy()
        df_ref["diff"] = (df_ref["timestamp"] - target_time).abs()
        closest_idx = df_ref["diff"].idxmin()
        reference = df_ref.loc[closest_idx]
        
        def get_trend_str(metric: str) -> str:
            curr_val = getattr(current, metric, None)
            ref_val = reference.get(metric) if pd.notnull(reference.get(metric)) else None
            if curr_val is None or ref_val is None:
                return "stable"
            return compute_trend(curr_val, ref_val)
            
        pressure_curr = current.pressure
        pressure_ref = reference.get("pressure") if pd.notnull(reference.get("pressure")) else None
        
        if pressure_curr is not None and pressure_ref is not None:
            pressure_change = pressure_curr - pressure_ref
            rain_alert = compute_rain_alert(pressure_change)
        else:
            pressure_change = None
            rain_alert = False
            
        return TrendInfo(
            temperature=get_trend_str("temperature"),
            humidity=get_trend_str("humidity"),
            pressure=get_trend_str("pressure"),
            pressure_change_hpa=pressure_change,
            rain_alert=rain_alert
        )

class GetAgroIndices:
    """Use case: retorna os índices agrometeorológicos calculados."""

    def __init__(self, repository: CSVRepository) -> None:
        self._repository = repository

    async def execute(self, start: date | None, end: date | None) -> list[AgroIndex]:
        df = await self._repository.fetch_agro_indices()

        if df.empty:
            return []

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        if start:
            df = df[df["date"] >= start]
        if end:
            df = df[df["date"] <= end]

        df["date"] = df["date"].astype(str)

        df = df.astype(object).where(pd.notnull(df), None)

        return [AgroIndex(**row) for row in df.to_dict(orient="records")]