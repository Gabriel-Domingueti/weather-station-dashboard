from datetime import date, datetime, timedelta, timezone

import pandas as pd

from app.core.cache import DataCache
from app.domain.agrometeorology import SUL_DE_MINAS_CITY_NAMES, evaluate_all_phytosanitary_alerts
from app.domain.models import (
    AgroIndex,
    DailySummary,
    MetricRecord,
    MetricType,
    MonthlyRecords,
    PhytosanitaryReport,
    TrendInfo,
    WeatherReading,
)
from app.infrastructure.csv_repository import CSVRepository
from app.infrastructure.thingspeak_client import ThingSpeakClient


def compute_staleness(reading_timestamp, now, threshold_minutes: int) -> tuple[bool, float]:
    """Retorna (esta_desatualizado, minutos_desde_a_leitura)."""
    delta = now - reading_timestamp
    minutes = delta.total_seconds() / 60.0
    is_stale = minutes >= threshold_minutes
    return is_stale, minutes


class GetLatestReading:
    """Use case: retorna a condição atual (do ThingSpeak ou do dataset da cidade selecionada)."""

    def __init__(
        self,
        thingspeak_client: ThingSpeakClient,
        repository: CSVRepository | None = None,
    ) -> None:
        self._thingspeak_client = thingspeak_client
        self._repository = repository

    async def execute(self, city: str | None = None) -> WeatherReading | None:
        if city and self._repository and hasattr(self._repository, "fetch_city_raw_data"):
            df = await self._repository.fetch_city_raw_data(city)
            if not df.empty:
                df_valid = df.dropna(subset=["temperature", "humidity", "pressure"], how="all")
                if not df_valid.empty:
                    last_row = df_valid.iloc[-1]
                    return WeatherReading(
                        timestamp=last_row["timestamp"],
                        temperature=float(last_row["temperature"]) if pd.notnull(last_row["temperature"]) else None,
                        humidity=float(last_row["humidity"]) if pd.notnull(last_row["humidity"]) else None,
                        pressure=float(last_row["pressure"]) if pd.notnull(last_row["pressure"]) else None,
                    )

        return await self._thingspeak_client.get_latest()


class GetDailySummary:
    """Use case: retorna o resumo diário (histórico agregado), do cache ou da cidade selecionada."""

    def __init__(self, cache: DataCache, repository: CSVRepository | None = None) -> None:
        self._cache = cache
        self._repository = repository

    async def execute(
        self, start: date | None, end: date | None, city: str | None = None
    ) -> list[DailySummary]:
        df = pd.DataFrame()
        if city and self._repository and hasattr(self._repository, "fetch_city_daily_data"):
            city_df = await self._repository.fetch_city_daily_data(city)
            if not city_df.empty:
                summary_cols = [
                    "date",
                    "temperature_avg", "temperature_min", "temperature_max",
                    "humidity_avg", "humidity_min", "humidity_max",
                    "pressure_avg", "pressure_min", "pressure_max",
                ]
                available_cols = [c for c in summary_cols if c in city_df.columns]
                df = city_df[available_cols].copy()

        if df.empty:
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
        df = df.astype(object).where(pd.notnull(df), None)

        return [DailySummary(**row) for row in df.to_dict(orient="records")]


class GetHistoricalReadings:
    """Use case: retorna leituras brutas (não agregadas) de um período/métrica/cidade."""

    def __init__(self, repository: CSVRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        start: date,
        end: date,
        metric: MetricType | None = None,
        city: str | None = None,
    ) -> list[WeatherReading]:
        if city and hasattr(self._repository, "fetch_city_raw_range"):
            df = await self._repository.fetch_city_raw_range(city, start, end)
        else:
            df = await self._repository.fetch_raw_range(start, end)

        if df.empty:
            return []

        if metric:
            columns = ["timestamp", metric.value]
            df = df[columns]

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
    def __init__(self, cache: DataCache, repository: CSVRepository | None = None) -> None:
        self._cache = cache
        self._repository = repository

    async def execute(
        self, year: int, month: int, city: str | None = None
    ) -> MonthlyRecords:
        df = pd.DataFrame()
        if city and self._repository and hasattr(self._repository, "fetch_city_daily_data"):
            df = await self._repository.fetch_city_daily_data(city)

        if df.empty:
            await self._cache.ensure_fresh()
            df = self._cache.daily_summary

        month_str = f"{year:04d}-{month:02d}"

        empty_record = MetricRecord(max_value=None, max_date=None, min_value=None, min_date=None)
        if df.empty:
            return MonthlyRecords(
                month=month_str,
                temperature=empty_record,
                humidity=empty_record,
                pressure=empty_record,
            )

        df = df.copy()
        df["date_str"] = df["date"].astype(str)
        df_month = df[df["date_str"].str.startswith(month_str)]

        if df_month.empty:
            return MonthlyRecords(
                month=month_str,
                temperature=empty_record,
                humidity=empty_record,
                pressure=empty_record,
            )

        def get_metric_record(metric_prefix: str) -> MetricRecord:
            max_col = f"{metric_prefix}_max"
            min_col = f"{metric_prefix}_min"

            valid_max = df_month[pd.notnull(df_month[max_col])]
            if valid_max.empty:
                max_val = None
                max_date = None
            else:
                max_idx = valid_max[max_col].idxmax()
                max_val = valid_max.loc[max_idx, max_col]
                max_date = valid_max.loc[max_idx, "date_str"]

            valid_min = df_month[pd.notnull(df_month[min_col])]
            if valid_min.empty:
                min_val = None
                min_date = None
            else:
                min_idx = valid_min[min_col].idxmin()
                min_val = valid_min.loc[min_idx, min_col]
                min_date = valid_min.loc[min_idx, "date_str"]

            return MetricRecord(
                max_value=max_val,
                max_date=max_date,
                min_value=min_val,
                min_date=min_date,
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

    async def execute(self, city: str | None = None) -> TrendInfo:
        default_trend = TrendInfo(temperature="stable", humidity="stable", pressure="stable")

        if city and hasattr(self._repository, "fetch_city_raw_data"):
            df_city = await self._repository.fetch_city_raw_data(city)
            df_valid = df_city.dropna(subset=["temperature", "humidity", "pressure"], how="all")
            if len(df_valid) >= 4:
                current_row = df_valid.iloc[-1]
                reference_row = df_valid.iloc[-4]  # 3 horas antes (dados horários)

                def city_trend(metric: str) -> str:
                    c_val = current_row.get(metric)
                    r_val = reference_row.get(metric)
                    if pd.isna(c_val) or pd.isna(r_val):
                        return "stable"
                    return compute_trend(float(c_val), float(r_val))

                p_curr = current_row.get("pressure")
                p_ref = reference_row.get("pressure")
                if pd.notnull(p_curr) and pd.notnull(p_ref):
                    p_change = round(float(p_curr) - float(p_ref), 2)
                    rain_alert = compute_rain_alert(p_change)
                else:
                    p_change = None
                    rain_alert = False

                return TrendInfo(
                    temperature=city_trend("temperature"),
                    humidity=city_trend("humidity"),
                    pressure=city_trend("pressure"),
                    pressure_change_hpa=p_change,
                    rain_alert=rain_alert,
                )

        current = await self._thingspeak.get_latest()
        if not current:
            return default_trend

        now = datetime.now(timezone.utc)
        ref_time_end = now - timedelta(hours=2, minutes=30)
        ref_time_start = now - timedelta(hours=3, minutes=30)

        df = await self._repository.fetch_raw_range(ref_time_start.date(), ref_time_end.date())
        if df.empty:
            return default_trend

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df_ref = df[(df["timestamp"] >= ref_time_start) & (df["timestamp"] <= ref_time_end)]
        if df_ref.empty:
            return default_trend

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
            rain_alert=rain_alert,
        )


class GetAgroIndices:
    """Use case: retorna os índices agrometeorológicos calculados."""

    def __init__(self, repository: CSVRepository) -> None:
        self._repository = repository

    async def execute(
        self, start: date | None, end: date | None, city: str | None = None
    ) -> list[AgroIndex]:
        df = pd.DataFrame()
        if city and hasattr(self._repository, "fetch_city_daily_data"):
            city_df = await self._repository.fetch_city_daily_data(city)
            if not city_df.empty and {"date", "gd", "gd_acumulado", "dmf_hours"}.issubset(city_df.columns):
                df = city_df[["date", "gd", "gd_acumulado", "dmf_hours"]].copy()

        if df.empty:
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


class GetPhytosanitaryAlerts:
    """
    Use case: combina o resumo diário (temperaturas, umidade, pressão) e os
    índices agrometeorológicos (GD acumulado e DMF) com as leituras horárias
    recentes para gerar o boletim de alerta de doenças e pragas do cafeeiro.
    """

    def __init__(self, repository: CSVRepository) -> None:
        self._repository = repository

    async def execute(
        self, target_date: date | None = None, city: str | None = None
    ) -> PhytosanitaryReport:
        city_key = (city or "varginha").strip().lower()
        city_label = SUL_DE_MINAS_CITY_NAMES.get(city_key, "Varginha")
        region_name = f"Sul de Minas Gerais ({city_label})"

        merged = pd.DataFrame()
        if hasattr(self._repository, "fetch_city_daily_data"):
            city_df = await self._repository.fetch_city_daily_data(city_key)
            if not city_df.empty and "date" in city_df.columns:
                merged = city_df.copy()

        if merged.empty:
            summary_df = await self._repository.fetch_daily_summary()
            indices_df = await self._repository.fetch_agro_indices()

            if summary_df.empty or indices_df.empty:
                report_dict = evaluate_all_phytosanitary_alerts(
                    daily_rows=[], raw_readings=[], region_name=region_name
                )
                return PhytosanitaryReport(**report_dict)

            summary_df = summary_df.copy()
            indices_df = indices_df.copy()
            summary_df["date"] = summary_df["date"].astype(str)
            indices_df["date"] = indices_df["date"].astype(str)
            merged = pd.merge(summary_df, indices_df, on="date", how="inner")

        merged["date"] = merged["date"].astype(str)
        if target_date is not None:
            merged = merged[merged["date"] <= target_date.isoformat()]

        if merged.empty:
            report_dict = evaluate_all_phytosanitary_alerts(
                daily_rows=[], raw_readings=[], region_name=region_name
            )
            return PhytosanitaryReport(**report_dict)

        merged = merged.sort_values("date").reset_index(drop=True)
        merged = merged.astype(object).where(pd.notnull(merged), None)
        daily_rows = merged.to_dict(orient="records")

        latest_date_str = str(daily_rows[-1]["date"])
        end_dt = date.fromisoformat(latest_date_str)
        start_dt = end_dt - timedelta(days=7)

        raw_readings: list[dict] = []
        if hasattr(self._repository, "fetch_city_raw_range"):
            raw_df = await self._repository.fetch_city_raw_range(city_key, start_dt, end_dt)
            if not raw_df.empty:
                raw_df = raw_df.astype(object).where(pd.notnull(raw_df), None)
                raw_readings = raw_df.to_dict(orient="records")
        elif city_key == "varginha" and hasattr(self._repository, "fetch_raw_range"):
            raw_df = await self._repository.fetch_raw_range(start_dt, end_dt)
            if not raw_df.empty:
                raw_df = raw_df.astype(object).where(pd.notnull(raw_df), None)
                raw_readings = raw_df.to_dict(orient="records")

        report_dict = evaluate_all_phytosanitary_alerts(
            daily_rows=daily_rows,
            raw_readings=raw_readings,
            region_name=region_name,
        )
        return PhytosanitaryReport(**report_dict)
