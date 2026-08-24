"""
ETL executado pelo GitHub Actions (.github/workflows/sync-data.yml).

1. Busca no ThingSpeak as leituras desde o último checkpoint salvo.
2. Anexa aos CSVs mensais em data/raw/YYYY-MM.csv.
3. Recalcula o resumo diário em data/aggregated/daily_summary.csv.

Não depende de banco de dados: o próprio CSV serve de checkpoint
(a última linha já commitada indica de onde continuar).
"""

import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

THINGSPEAK_CHANNEL_ID = os.environ["THINGSPEAK_CHANNEL_ID"]
THINGSPEAK_READ_API_KEY = os.environ.get("THINGSPEAK_READ_API_KEY", "")

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
AGGREGATED_DIR = REPO_ROOT / "data" / "aggregated"

FIELD_MAP = {
    "field1": "temperature",
    "field2": "humidity",
    "field3": "pressure",
}


def fetch_new_readings(since: datetime | None) -> pd.DataFrame:
    url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"
    params: dict[str, str] = {"results": "8000"}
    if THINGSPEAK_READ_API_KEY:
        params["api_key"] = THINGSPEAK_READ_API_KEY
    if since:
        params["start"] = since.strftime("%Y-%m-%d %H:%M:%S")

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    feeds = response.json().get("feeds", [])

    if not feeds:
        return pd.DataFrame(columns=["timestamp", "temperature", "humidity", "pressure"])

    df = pd.DataFrame(feeds).rename(columns=FIELD_MAP)

    # O ThingSpeak devolve created_at com timezone (UTC, ex: "...Z").
    # Os timestamps já salvos no CSV são naive (sem timezone). Normaliza
    # aqui pra naive logo na entrada, senão a comparação com o checkpoint
    # (`> since`) quebra com "Cannot compare tz-naive and tz-aware".
    df["timestamp"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)

    columns = ["timestamp", "temperature", "humidity", "pressure"]
    return df[columns].dropna(subset=["timestamp"])


def last_checkpoint() -> datetime | None:
    if not RAW_DIR.exists():
        return None
    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        return None

    latest_file = csv_files[-1]
    df = pd.read_csv(latest_file)
    if df.empty:
        return None
    return pd.to_datetime(df["timestamp"]).max().to_pydatetime()


def append_to_monthly_csv(df: pd.DataFrame) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    df["year_month"] = df["timestamp"].dt.strftime("%Y-%m")

    for year_month, group in df.groupby("year_month"):
        file_path = RAW_DIR / f"{year_month}.csv"
        group = group.drop(columns=["year_month"])

        if file_path.exists():
            existing = pd.read_csv(file_path)
            existing["timestamp"] = pd.to_datetime(existing["timestamp"])
            combined = pd.concat([existing, group]).drop_duplicates(subset=["timestamp"])
        else:
            combined = group

        combined = combined.sort_values("timestamp")
        combined.to_csv(file_path, index=False)
        print(f"  {file_path.name}: {len(combined)} linhas")


def rebuild_daily_summary() -> None:
    AGGREGATED_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        return

    all_readings = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
    all_readings["timestamp"] = pd.to_datetime(all_readings["timestamp"])
    all_readings["date"] = all_readings["timestamp"].dt.date

    summary = all_readings.groupby("date").agg(
        temperature_avg=("temperature", "mean"),
        temperature_min=("temperature", "min"),
        temperature_max=("temperature", "max"),
        humidity_avg=("humidity", "mean"),
        humidity_min=("humidity", "min"),
        humidity_max=("humidity", "max"),
        pressure_avg=("pressure", "mean"),
        pressure_min=("pressure", "min"),
        pressure_max=("pressure", "max"),
    ).round(2).reset_index()

    summary.to_csv(AGGREGATED_DIR / "daily_summary.csv", index=False)
    print(f"  daily_summary.csv: {len(summary)} dias")


def main() -> None:
    since = last_checkpoint()
    print(f"Buscando leituras desde: {since or 'início'}")

    new_readings = fetch_new_readings(since)
    if since is not None:
        new_readings = new_readings[new_readings["timestamp"] > since]

    if new_readings.empty:
        print("Nenhuma leitura nova.")
        return

    print(f"{len(new_readings)} leituras novas encontradas.")
    append_to_monthly_csv(new_readings)
    rebuild_daily_summary()
    print(f"Sincronização concluída em {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()