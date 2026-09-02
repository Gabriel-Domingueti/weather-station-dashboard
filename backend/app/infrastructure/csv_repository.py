import logging
from datetime import date
from io import StringIO
from pathlib import Path

import httpx
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)


class CSVRepository:
    """
    Porta de acesso aos dados históricos.
    Busca do GitHub raw em produção, ou do diretório local data/ como fallback.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None, data_dir: Path | None = None) -> None:
        self._client = http_client or httpx.AsyncClient(timeout=15.0)
        self._data_dir = data_dir or self._resolve_data_dir()

    def _resolve_data_dir(self) -> Path:
        custom_dir = Path(settings.local_data_dir)
        if custom_dir.exists():
            return custom_dir
        # Check workspace root data dir
        root_data = Path(__file__).resolve().parent.parent.parent.parent / "data"
        if root_data.exists():
            return root_data
        return custom_dir

    async def fetch_daily_summary(self) -> pd.DataFrame:
        if settings.github_owner != "seu-usuario":
            url = f"{settings.raw_base_url}/aggregated/daily_summary.csv"
            try:
                return await self._fetch_csv(url)
            except Exception as e:
                logger.warning("Falha ao buscar do GitHub (%s), tentando arquivo local...", e)

        local_file = self._data_dir / "aggregated" / "daily_summary.csv"
        if local_file.exists():
            return pd.read_csv(local_file)

        return pd.DataFrame(columns=[
            "date", "temperature_avg", "temperature_min", "temperature_max",
            "humidity_avg", "humidity_min", "humidity_max",
            "pressure_avg", "pressure_min", "pressure_max"
        ])

    async def fetch_raw_month(self, year: int, month: int) -> pd.DataFrame:
        if settings.github_owner != "seu-usuario":
            url = f"{settings.raw_base_url}/raw/{year:04d}-{month:02d}.csv"
            try:
                return await self._fetch_csv(url)
            except Exception:
                pass

        local_file = self._data_dir / "raw" / f"{year:04d}-{month:02d}.csv"
        if local_file.exists():
            return pd.read_csv(local_file)

        return pd.DataFrame(columns=["timestamp", "temperature", "humidity", "pressure"])

    async def fetch_raw_range(self, start: date, end: date) -> pd.DataFrame:
        """Busca e concatena todos os CSVs mensais que cobrem o intervalo pedido."""
        months: list[tuple[int, int]] = []
        cursor = date(start.year, start.month, 1)
        while cursor <= end:
            months.append((cursor.year, cursor.month))
            cursor = date(
                cursor.year + (cursor.month == 12),
                1 if cursor.month == 12 else cursor.month + 1,
                1,
            )

        frames = []
        for year, month in months:
            df_month = await self.fetch_raw_month(year, month)
            if not df_month.empty:
                frames.append(df_month)

        if not frames:
            return pd.DataFrame(columns=["timestamp", "temperature", "humidity", "pressure"])

        df = pd.concat(frames, ignore_index=True)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="mixed")
        mask = (df["timestamp"].dt.date >= start) & (df["timestamp"].dt.date <= end)
        return df.loc[mask].sort_values("timestamp").reset_index(drop=True)

    async def _fetch_csv(self, url: str) -> pd.DataFrame:
        response = await self._client.get(url)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))

    async def fetch_agro_indices(self) -> pd.DataFrame:
        if settings.github_owner != "seu-usuario":
            url = f"{settings.raw_base_url}/aggregated/agrometeorological_indices.csv"
            try:
                return await self._fetch_csv(url)
            except Exception as e:
                logger.warning("Falha ao buscar índices do GitHub (%s), tentando arquivo local...", e)

        local_file = self._data_dir / "aggregated" / "agrometeorological_indices.csv"
        if local_file.exists():
            return pd.read_csv(local_file)

        return pd.DataFrame(columns=[
            "date", "gd", "gd_acumulado", "dmf_hours"
        ])