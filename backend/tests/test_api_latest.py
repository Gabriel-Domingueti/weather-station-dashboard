import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.infrastructure.thingspeak_client import ThingSpeakClient
from app.domain.models import WeatherReading

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_get_latest_reading_is_stale(client, monkeypatch):
    # Setup mock to return a stale reading (e.g. 1 hour ago)
    now = datetime.now(timezone.utc)
    stale_time = now - timedelta(hours=1)
    
    mock_reading = WeatherReading(
        timestamp=stale_time,
        temperature=25.0,
        humidity=60.0,
        pressure=1013.0
    )
    
    async def mock_get_latest(*args, **kwargs):
        return mock_reading
        
    monkeypatch.setattr(ThingSpeakClient, "get_latest", mock_get_latest)
    
    # Execute request
    response = client.get("/api/readings/latest")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["is_stale"] is True
    assert data["minutes_since_reading"] >= 60.0
    assert data["reading"]["temperature"] == 25.0

@pytest.mark.asyncio
async def test_get_latest_reading_none(client, monkeypatch):
    # Setup mock to return None (no readings at all)
    async def mock_get_latest(*args, **kwargs):
        return None
        
    monkeypatch.setattr(ThingSpeakClient, "get_latest", mock_get_latest)
    
    # Execute request
    response = client.get("/api/readings/latest")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["is_stale"] is True
    assert data["minutes_since_reading"] is None
    assert data["reading"] is None
