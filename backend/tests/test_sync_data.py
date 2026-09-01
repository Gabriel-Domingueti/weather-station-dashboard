import os
import sys
from pathlib import Path
import pandas as pd
import pytest

# Adicionar a raiz do projeto ao PYTHONPATH para importar scripts.sync_data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["THINGSPEAK_CHANNEL_ID"] = "123"
from scripts import sync_data

def test_rebuild_daily_summary(tmp_path, sample_readings_df, monkeypatch):
    raw_dir = tmp_path / "data" / "raw"
    agg_dir = tmp_path / "data" / "aggregated"
    raw_dir.mkdir(parents=True)
    agg_dir.mkdir(parents=True)
    monkeypatch.setattr(sync_data, "RAW_DIR", raw_dir)
    monkeypatch.setattr(sync_data, "AGGREGATED_DIR", agg_dir)

    edge_case_data = [
        {"timestamp": pd.to_datetime("2026-08-03 10:00:00", utc=True), "temperature": None, "humidity": 50.0, "pressure": 1010.0},
        {"timestamp": pd.to_datetime("2026-08-03 11:00:00", utc=True), "temperature": None, "humidity": 55.0, "pressure": 1011.0},
    ]
    df = pd.concat([sample_readings_df, pd.DataFrame(edge_case_data)], ignore_index=True)
    df.to_csv(raw_dir / "2026-08.csv", index=False)

    sync_data.rebuild_daily_summary()

    summary_file = agg_dir / "daily_summary.csv"
    assert summary_file.exists()

    summary = pd.read_csv(summary_file)
    assert len(summary) == 3 # Dia 1, Dia 2, Dia 3

    day1 = summary[summary["date"] == "2026-08-01"].iloc[0]
    assert day1["temperature_avg"] == 26.0
    assert day1["humidity_avg"] == 57.5 
    
    day3 = summary[summary["date"] == "2026-08-03"].iloc[0]
    assert pd.isna(day3["temperature_avg"]) or day3["temperature_avg"] is None

def test_append_to_monthly_csv(tmp_path, sample_readings_df, monkeypatch):
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    monkeypatch.setattr(sync_data, "RAW_DIR", raw_dir)

    # Executa a primeira vez
    sync_data.append_to_monthly_csv(sample_readings_df)
    
    file_path = raw_dir / "2026-08.csv"
    assert file_path.exists()
    
    saved_df_1 = pd.read_csv(file_path)
    assert len(saved_df_1) == 5

    # Executa a segunda vez com os mesmos dados + 1 linha nova
    new_data = [
        {"timestamp": pd.to_datetime("2026-08-02 12:00:00", utc=True), "temperature": 23.0, "humidity": 68.0, "pressure": 1014.5}
    ]
    new_df = pd.concat([sample_readings_df, pd.DataFrame(new_data)], ignore_index=True)
    
    sync_data.append_to_monthly_csv(new_df)
    
    saved_df_2 = pd.read_csv(file_path)
    # Deve conter 6 linhas (5 originais + 1 nova), sem duplicações das 5 originais
    assert len(saved_df_2) == 6

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
    def json(self):
        return self.json_data
    def raise_for_status(self):
        pass

def mock_requests_get(url, params=None, timeout=None):
    return MockResponse({
        "channel": {"id": 123},
        "feeds": [
            {
                "created_at": "2026-09-01T21:18:00Z",
                "entry_id": 1,
                "field1": "25.0",
                "field2": "60.0",
                "field3": "1012.0"
            }
        ]
    })

def test_fetch_new_readings_timezone(monkeypatch):
    import requests
    import datetime
    monkeypatch.setattr(requests, "get", mock_requests_get)
    
    df = sync_data.fetch_new_readings(since=None)
    
    assert not df.empty
    assert "timestamp" in df.columns
    assert df["timestamp"].dt.tz is not None

def test_last_checkpoint_naive_csv(tmp_path, monkeypatch):
    import datetime
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    monkeypatch.setattr(sync_data, "RAW_DIR", raw_dir)

    # Cria CSV com timestamp naive
    csv_content = "timestamp,temperature,humidity,pressure\n2026-09-01 21:18:00,25.0,60.0,1012.0"
    (raw_dir / "2026-09.csv").write_text(csv_content)

    checkpoint = sync_data.last_checkpoint()
    
    assert checkpoint is not None
    assert checkpoint.tzinfo is not None
    
    nova_data = datetime.datetime(2026, 9, 1, 22, 18, 0, tzinfo=datetime.timezone.utc)
    # Não deve lançar TypeError
    assert nova_data > checkpoint
