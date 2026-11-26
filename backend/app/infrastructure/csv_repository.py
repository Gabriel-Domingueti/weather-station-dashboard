import logging
from datetime import date, datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import httpx
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)

# Cache em memória por chave de arquivo para evitar múltiplos downloads do GitHub Raw
_CITY_DF_CACHE: dict[str, tuple[datetime, pd.DataFrame]] = {}
_CACHE_TTL = timedelta(minutes=30)


def clear_city_cache() -> None:
    """Limpa o cache em memória de todas as cidades do Sul de Minas."""
    _CITY_DF_CACHE.clear()


def clean_csv_content(raw_text: str) -> str:
    """
    Remove marcadores de conflito de merge do Git (<<<<<<<, =======, >>>>>>>)
    e cabeçalhos duplicados caso algum arquivo CSV tenha sofrido merge manual.
    """
    lines = raw_text.splitlines()
    cleaned: list[str] = []
    header_seen: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if (
            stripped.startswith("<<<<<<<")
            or stripped.startswith("=======")
            or stripped.startswith(">>>>>>>")
        ):
            continue
        if header_seen is None:
            header_seen = stripped
            cleaned.append(stripped)
        elif stripped == header_seen:
            continue
        else:
            cleaned.append(stripped)

    return "\n".join(cleaned)


def read_csv_safely(source_text_or_path: str | Path, is_path: bool = False) -> pd.DataFrame:
    if is_path:
        raw_text = Path(source_text_or_path).read_text(encoding="utf-8", errors="replace")
    else:
        raw_text = str(source_text_or_path)

    cleaned = clean_csv_content(raw_text)
    if not cleaned:
        return pd.DataFrame()

    df = pd.read_csv(StringIO(cleaned))
    if "date" in df.columns:
        df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    elif "timestamp" in df.columns:
        df = df.drop_duplicates(subset=["timestamp"], keep="last").reset_index(drop=True)
    return df


class CSVRepository:
    """
    Porta de acesso aos dados históricos.
    Busca do diretório local data/ quando disponível, ou do GitHub raw em produção.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None, data_dir: Path | None = None) -> None:
        self._client = http_client or httpx.AsyncClient(timeout=20.0)
        self._data_dir = data_dir or self._resolve_data_dir()

    def _resolve_data_dir(self) -> Path:
        custom_dir = Path(settings.local_data_dir)
        if custom_dir.exists():
            return custom_dir
        root_data = Path(__file__).resolve().parent.parent.parent.parent / "data"
        if root_data.exists():
            return root_data
        return custom_dir

    async def fetch_daily_summary(self) -> pd.DataFrame:
        local_file = self._data_dir / "aggregated" / "daily_summary.csv"
        if local_file.exists():
            try:
                df = read_csv_safely(local_file, is_path=True)
                if not df.empty and "date" in df.columns:
                    return df
            except Exception as e:
                logger.warning("Falha ao ler daily_summary local (%s)...", e)

        if settings.github_owner != "seu-usuario":
            url = f"{settings.raw_base_url}/aggregated/daily_summary.csv"
            try:
                df = await self._fetch_csv(url)
                if not df.empty and "date" in df.columns:
                    return df
            except Exception as e:
                logger.warning("Falha ao buscar do GitHub (%s)...", e)

        return pd.DataFrame(columns=[
            "date", "temperature_avg", "temperature_min", "temperature_max",
            "humidity_avg", "humidity_min", "humidity_max",
            "pressure_avg", "pressure_min", "pressure_max"
        ])

    async def fetch_raw_month(self, year: int, month: int) -> pd.DataFrame:
        local_file = self._data_dir / "raw" / f"{year:04d}-{month:02d}.csv"
        if local_file.exists():
            try:
                df = read_csv_safely(local_file, is_path=True)
                if not df.empty and "timestamp" in df.columns:
                    return df
            except Exception:
                pass

        if settings.github_owner != "seu-usuario":
            url = f"{settings.raw_base_url}/raw/{year:04d}-{month:02d}.csv"
            try:
                df = await self._fetch_csv(url)
                if not df.empty and "timestamp" in df.columns:
                    return df
            except Exception:
                pass

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
        return read_csv_safely(response.text, is_path=False)

    async def fetch_agro_indices(self) -> pd.DataFrame:
        local_file = self._data_dir / "aggregated" / "agrometeorological_indices.csv"
        if local_file.exists():
            try:
                df = read_csv_safely(local_file, is_path=True)
                if not df.empty and "date" in df.columns:
                    return df
            except Exception as e:
                logger.warning("Falha ao ler agro_indices local (%s)...", e)

        if settings.github_owner != "seu-usuario":
            url = f"{settings.raw_base_url}/aggregated/agrometeorological_indices.csv"
            try:
                df = await self._fetch_csv(url)
                if not df.empty and "date" in df.columns:
                    return df
            except Exception as e:
                logger.warning("Falha ao buscar índices do GitHub (%s)...", e)

        return pd.DataFrame(columns=[
            "date", "gd", "gd_acumulado", "dmf_hours"
        ])

    async def fetch_city_daily_data(self, city_key: str) -> pd.DataFrame:
        """
        Busca o resumo diário + índices agrometeorológicos pré-calculados de uma
        cidade específica do Sul de Minas (data/sul_de_minas/{city_key}_daily.csv).
        """
        safe_key = city_key.strip().lower()
        cache_key = f"daily:{safe_key}"
        now = datetime.now(timezone.utc)
        if cache_key in _CITY_DF_CACHE:
            ts, cached_df = _CITY_DF_CACHE[cache_key]
            if now - ts < _CACHE_TTL:
                return cached_df.copy()

        local_daily = self._data_dir / "sul_de_minas" / f"{safe_key}_daily.csv"
        if local_daily.exists():
            try:
                df = read_csv_safely(local_daily, is_path=True)
                if not df.empty and "date" in df.columns:
                    _CITY_DF_CACHE[cache_key] = (now, df)
                    return df.copy()
            except Exception as e:
                logger.warning("Falha ao ler %s local (%s)...", local_daily.name, e)

        if settings.github_owner != "seu-usuario":
            url = f"{settings.raw_base_url}/sul_de_minas/{safe_key}_daily.csv"
            try:
                df = await self._fetch_csv(url)
                if not df.empty and "date" in df.columns:
                    _CITY_DF_CACHE[cache_key] = (now, df)
                    return df.copy()
            except Exception as e:
                logger.warning("Falha ao buscar %s do GitHub (%s)...", url, e)

        return pd.DataFrame()

    async def fetch_city_raw_data(self, city_key: str) -> pd.DataFrame:
        """
        Busca a série horária completa de uma cidade do Sul de Minas
        (data/sul_de_minas/{city_key}.csv) com cache em memória.
        """
        safe_key = city_key.strip().lower()
        cache_key = f"raw:{safe_key}"
        now = datetime.now(timezone.utc)
        if cache_key in _CITY_DF_CACHE:
            ts, cached_df = _CITY_DF_CACHE[cache_key]
            if now - ts < _CACHE_TTL:
                return cached_df.copy()

        local_raw = self._data_dir / "sul_de_minas" / f"{safe_key}.csv"
        if local_raw.exists():
            try:
                df = read_csv_safely(local_raw, is_path=True)
                if not df.empty and "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="mixed")
                    df = df.sort_values("timestamp").reset_index(drop=True)
                    _CITY_DF_CACHE[cache_key] = (now, df)
                    return df.copy()
            except Exception as e:
                logger.warning("Falha ao ler %s local (%s)...", local_raw.name, e)

        if settings.github_owner != "seu-usuario":
            url = f"{settings.raw_base_url}/sul_de_minas/{safe_key}.csv"
            try:
                df = await self._fetch_csv(url)
                if not df.empty and "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="mixed")
                    df = df.sort_values("timestamp").reset_index(drop=True)
                    _CITY_DF_CACHE[cache_key] = (now, df)
                    return df.copy()
            except Exception as e:
                logger.warning("Falha ao buscar %s do GitHub (%s)...", url, e)

        return pd.DataFrame(columns=["timestamp", "temperature", "humidity", "pressure"])

    async def fetch_city_raw_range(self, city_key: str, start: date, end: date) -> pd.DataFrame:
        df = await self.fetch_city_raw_data(city_key)
        if df.empty:
            return pd.DataFrame(columns=["timestamp", "temperature", "humidity", "pressure"])
        mask = (df["timestamp"].dt.date >= start) & (df["timestamp"].dt.date <= end)
        return df.loc[mask].sort_values("timestamp").reset_index(drop=True)
