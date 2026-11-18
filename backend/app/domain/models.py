from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class MetricType(str, Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"


class WeatherReading(BaseModel):
    """Uma leitura pontual da estação (linha do CSV ou do ThingSpeak)."""

    timestamp: datetime
    temperature: float | None = None
    humidity: float | None = None
    pressure: float | None = None


class DailySummary(BaseModel):
    """Resumo agregado de um dia (min/max/média por métrica)."""

    date: str
    temperature_avg: float | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    humidity_avg: float | None = None
    humidity_min: float | None = None
    humidity_max: float | None = None
    pressure_avg: float | None = None
    pressure_min: float | None = None
    pressure_max: float | None = None


class LatestReadingResponse(BaseModel):
    reading: WeatherReading | None
    is_stale: bool
    minutes_since_reading: float | None

class MetricRecord(BaseModel):
    max_value: float | None
    max_date: str | None
    min_value: float | None
    min_date: str | None

class MonthlyRecords(BaseModel):
    month: str  # formato "YYYY-MM"
    temperature: MetricRecord
    humidity: MetricRecord
    pressure: MetricRecord

class TrendInfo(BaseModel):
    temperature: str
    humidity: str
    pressure: str
    pressure_change_hpa: float | None = None
    rain_alert: bool = False

class AgroIndex(BaseModel):
    date: str
    gd: float | None = None
    gd_acumulado: float | None = None
    dmf_hours: float | None = None


class CoffeePhenology(BaseModel):
    nodes_per_branch: float
    leafiness_pct: float


class PhytosanitaryAlertItem(BaseModel):
    disease_key: str
    name: str
    scientific_name: str
    risk_level: str  # "low" | "moderate" | "high"
    status_label: str
    risk_score: float
    estimated_incidence_pct: float
    control_threshold_pct: float | None = None
    audpc_index: float | None = None
    germ_tube_length_um: float | None = None
    favorable_conditions: str
    recommendation: str
    references: list[str]


class PhytosanitaryReport(BaseModel):
    reference_date: str | None = None
    region: str
    gd_acumulado: float
    dmf_last_24h: float
    dmf_last_48h: float
    phenology: CoffeePhenology
    alerts: list[PhytosanitaryAlertItem]

