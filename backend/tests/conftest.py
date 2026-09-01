import pytest
import pandas as pd
from datetime import datetime

@pytest.fixture
def sample_readings_df():
    data = [
        {"timestamp": datetime(2026, 8, 1, 10, 0), "temperature": 25.0, "humidity": 60.0, "pressure": 1012.0},
        {"timestamp": datetime(2026, 8, 1, 11, 0), "temperature": 26.0, "humidity": None, "pressure": 1011.5},
        {"timestamp": datetime(2026, 8, 1, 12, 0), "temperature": 27.0, "humidity": 55.0, "pressure": 1010.0},
        {"timestamp": datetime(2026, 8, 2, 10, 0), "temperature": None, "humidity": 70.0, "pressure": 1015.0},
        {"timestamp": datetime(2026, 8, 2, 11, 0), "temperature": 22.0, "humidity": 65.0, "pressure": 1014.0},
    ]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df

@pytest.fixture
def mock_thingspeak_response():
    return {
        "channel": {
            "id": 123456,
            "name": "Estação Meteorológica",
            "field1": "Temperatura",
            "field2": "Umidade",
            "field3": "Pressão"
        },
        "feeds": [
            {
                "created_at": "2026-08-01T10:00:00Z",
                "entry_id": 1,
                "field1": "25.0",
                "field2": "60.0",
                "field3": "1012.0"
            },
            {
                "created_at": "2026-08-01T11:00:00Z",
                "entry_id": 2,
                "field1": "26.0",
                "field2": None,
                "field3": "1011.5"
            }
        ]
    }
