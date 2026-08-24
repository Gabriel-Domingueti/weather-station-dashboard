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
