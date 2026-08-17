import httpx

from app.config import settings
from app.domain.models import WeatherReading

# Ajuste esses números conforme os campos configurados no seu canal do ThingSpeak
FIELD_TEMPERATURE = "field1"
FIELD_HUMIDITY = "field2"
FIELD_PRESSURE = "field3"


class ThingSpeakClient:
    """Porta de acesso à leitura mais recente, direto do ThingSpeak."""

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._client = http_client or httpx.AsyncClient(timeout=10.0)

    async def get_latest(self) -> WeatherReading | None:
        if not settings.thingspeak_channel_id:
            return await self._get_latest_from_repository()

        url = f"https://api.thingspeak.com/channels/{settings.thingspeak_channel_id}/feeds/last.json"
        params = {"api_key": settings.thingspeak_read_api_key} if settings.thingspeak_read_api_key else {}

        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data or "created_at" not in data:
                return await self._get_latest_from_repository()

            return WeatherReading(
                timestamp=data["created_at"],
                temperature=_to_float(data.get(FIELD_TEMPERATURE)),
                humidity=_to_float(data.get(FIELD_HUMIDITY)),
                pressure=_to_float(data.get(FIELD_PRESSURE)),
            )
        except Exception:
            return await self._get_latest_from_repository()

    async def _get_latest_from_repository(self) -> WeatherReading | None:
        from app.infrastructure.csv_repository import CSVRepository
        from datetime import datetime
        now = datetime.now()
        df = await CSVRepository().fetch_raw_month(now.year, now.month)
        if df.empty:
            return None
        last_row = df.iloc[-1].to_dict()
        return WeatherReading(**last_row)


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
