import sys
from pathlib import Path
from datetime import date

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.use_cases import GetDailySummary, GetHistoricalReadings, compute_staleness, GetMonthlyRecords, compute_trend, compute_rain_alert, GetTrend
from datetime import datetime, timedelta, timezone
from app.domain.models import MetricType
from app.core.cache import DataCache


@pytest.mark.asyncio
async def test_get_daily_summary(sample_readings_df):
    # Resumo diário "de verdade": as mesmas colunas que GetDailySummary
    # espera de fato (temperature_avg/min/max etc.) — não os dados crus
    # de sample_readings_df reaproveitados com uma coluna "date" colada,
    # que era o que mascarava o teste antigo.
    daily_summary_data = [
        {
            "date": "2026-08-01",
            "temperature_avg": 24.0, "temperature_min": 22.0, "temperature_max": 26.0,
            "humidity_avg": 58.0, "humidity_min": 55.0, "humidity_max": 61.0,
            "pressure_avg": 1012.0, "pressure_min": 1010.0, "pressure_max": 1014.0,
        },
        {
            "date": "2026-08-02",
            "temperature_avg": 20.5, "temperature_min": 19.0, "temperature_max": 22.0,
            "humidity_avg": 66.0, "humidity_min": 63.0, "humidity_max": 69.0,
            "pressure_avg": 1015.5, "pressure_min": 1014.0, "pressure_max": 1017.0,
        },
        {
            # dia com uma métrica inteiramente ausente (simula um dia em que
            # o BME280 falhou ao ler pressão em todas as leituras)
            "date": "2026-08-03",
            "temperature_avg": 23.0, "temperature_min": 23.0, "temperature_max": 23.0,
            "humidity_avg": 50.0, "humidity_min": 50.0, "humidity_max": 50.0,
            "pressure_avg": None, "pressure_min": None, "pressure_max": None,
        },
    ]

    class MockCSVRepository:
        async def fetch_daily_summary(self):
            return pd.DataFrame(daily_summary_data)

    cache = DataCache(repository=MockCSVRepository())
    await cache.refresh()

    use_case = GetDailySummary(cache)

    # start=None, end=None -> todos os dias
    result_all = await use_case.execute(None, None)
    assert len(result_all) == 3

    # Filtro inclui os limites (bounds) e exclui fora do intervalo
    result_filtered = await use_case.execute(date(2026, 8, 2), date(2026, 8, 2))
    assert len(result_filtered) == 1
    assert result_filtered[0].date == "2026-08-02"

    # Os valores agregados de verdade precisam chegar corretos no objeto
    # final — não só a contagem de itens e a data. Isso é o que garante
    # que o mapeamento DataFrame -> DailySummary não quebrou silenciosamente
    # (o Pydantic ignora campos extras por padrão, então checar só
    # contagem/data não pegaria um bug aí).
    assert result_filtered[0].temperature_avg == 20.5
    assert result_filtered[0].temperature_min == 19.0
    assert result_filtered[0].humidity_max == 69.0
    assert result_filtered[0].pressure_min == 1014.0

    # Dia com métrica inteiramente ausente: precisa virar None, não NaN
    # (NaN não é JSON válido e quebraria o parse no front)
    day_3 = next(r for r in result_all if r.date == "2026-08-03")
    assert day_3.pressure_avg is None
    assert day_3.pressure_min is None
    assert day_3.pressure_max is None


@pytest.mark.asyncio
async def test_get_historical_readings(sample_readings_df):
    class MockCSVRepository:
        async def fetch_raw_range(self, start, end):
            return sample_readings_df

    repository = MockCSVRepository()
    use_case = GetHistoricalReadings(repository)

    result = await use_case.execute(date(2026, 8, 1), date(2026, 8, 2), MetricType.TEMPERATURE)

    assert len(result) == len(sample_readings_df)

    expected_temperatures = sample_readings_df["temperature"].tolist()
    for r, expected in zip(result, expected_temperatures):
        assert r.timestamp is not None

        # Comparação real contra o valor de entrada. A asserção antiga
        # (`r.temperature is not None or pd.isna(r.temperature) or
        # r.temperature is None`) era verdadeira pra qualquer valor
        # possível e não testava nada de fato.
        if pd.isna(expected):
            # precisa ser None de verdade, não NaN — NaN não é JSON válido
            assert r.temperature is None
        else:
            assert r.temperature == expected

        # humidity e pressure devem estar ausentes/nulos: a métrica
        # selecionada foi só TEMPERATURE
        assert getattr(r, "humidity", None) is None
        assert getattr(r, "pressure", None) is None

def test_compute_staleness():
    now = datetime(2026, 8, 23, 12, 0, 0, tzinfo=timezone.utc)
    
    # leitura de 5 minutos atrás com limiar de 30min -> não desatualizado
    recent_time = now - timedelta(minutes=5)
    is_stale, mins = compute_staleness(recent_time, now, 30)
    assert is_stale is False
    assert mins == 5.0
    
    # leitura de 45 minutos atrás com limiar de 30min -> desatualizado
    stale_time = now - timedelta(minutes=45)
    is_stale, mins = compute_staleness(stale_time, now, 30)
    assert is_stale is True
    assert mins == 45.0
    
    # leitura exatamente no limiar (30min e limiar 30min)
    # Decisão: será exclusive (se minutos_desde_a_leitura >= limiar, então é stale)
    # Assim, 30min exato com limiar 30 é stale.
    edge_time = now - timedelta(minutes=30)
    is_stale, mins = compute_staleness(edge_time, now, 30)
    assert is_stale is True
    assert mins == 30.0


def test_compute_trend():
    # stable
    assert compute_trend(25.0, 24.6, 0.5) == "stable"
    assert compute_trend(24.6, 25.0, 0.5) == "stable"
    assert compute_trend(25.0, 25.0, 0.5) == "stable"
    # exato no limiar (stable)
    assert compute_trend(25.5, 25.0, 0.5) == "stable"
    
    # rising
    assert compute_trend(25.6, 25.0, 0.5) == "rising"
    # falling
    assert compute_trend(24.4, 25.0, 0.5) == "falling"

    assert compute_trend(24.4, 25.0, 0.5) == "falling"


def test_compute_rain_alert():
    # queda de 5 hPa com limiar 3.5 -> True
    assert compute_rain_alert(-5.0, 3.5) is True
    # queda de 2 hPa com limiar 3.5 -> False
    assert compute_rain_alert(-2.0, 3.5) is False
    # subida de 5 hPa com limiar 3.5 -> False (não dispara em subida)
    assert compute_rain_alert(5.0, 3.5) is False
    # queda exatamente no limiar (-3.5 com limiar 3.5) -> decidi inclusive, portanto dispara (True)
    assert compute_rain_alert(-3.5, 3.5) is True

@pytest.mark.asyncio
async def test_get_monthly_records():
    # Mes de agosto
    daily_summary_data = [
        {
            "date": "2026-08-01",
            "temperature_avg": 24.0, "temperature_min": 22.0, "temperature_max": 26.0,
            "humidity_avg": 58.0, "humidity_min": 55.0, "humidity_max": 61.0,
            "pressure_avg": 1012.0, "pressure_min": 1010.0, "pressure_max": 1014.0,
        },
        {
            "date": "2026-08-02",
            "temperature_avg": 20.5, "temperature_min": 19.0, "temperature_max": 28.0, # max temp aqui
            "humidity_avg": 66.0, "humidity_min": 40.0, "humidity_max": 69.0, # min hum aqui
            "pressure_avg": 1015.5, "pressure_min": 1014.0, "pressure_max": 1017.0,
        },
        {
            "date": "2026-08-03",
            "temperature_avg": 23.0, "temperature_min": 10.0, "temperature_max": 23.0, # min temp aqui
            "humidity_avg": 50.0, "humidity_min": 50.0, "humidity_max": 80.0, # max hum aqui
            "pressure_avg": None, "pressure_min": None, "pressure_max": None,
        },
        {
            "date": "2026-09-01", # Outro mês
            "temperature_avg": 30.0, "temperature_min": 30.0, "temperature_max": 30.0,
            "humidity_avg": 90.0, "humidity_min": 90.0, "humidity_max": 90.0,
            "pressure_avg": 1000.0, "pressure_min": 1000.0, "pressure_max": 1000.0,
        }
    ]
    
    class MockCSVRepository:
        async def fetch_daily_summary(self):
            return pd.DataFrame(daily_summary_data)
            
    cache = DataCache(repository=MockCSVRepository())
    await cache.refresh()
    
    use_case = GetMonthlyRecords(cache)
    
    # 1. Normal data
    records_august = await use_case.execute(2026, 8)
    assert records_august.month == "2026-08"
    assert records_august.temperature.max_value == 28.0
    assert records_august.temperature.max_date == "2026-08-02"
    assert records_august.temperature.min_value == 10.0
    assert records_august.temperature.min_date == "2026-08-03"
    
    assert records_august.humidity.max_value == 80.0
    assert records_august.humidity.max_date == "2026-08-03"
    assert records_august.humidity.min_value == 40.0
    assert records_august.humidity.min_date == "2026-08-02"
    
    # 2. No data for month
    records_july = await use_case.execute(2026, 7)
    assert records_july.month == "2026-07"
    assert records_july.temperature.max_value is None
    assert records_july.temperature.max_date is None
    assert records_july.humidity.min_value is None

@pytest.mark.asyncio
async def test_get_trend():
    from app.domain.models import WeatherReading
    
    class MockThingSpeakClient:
        async def get_latest(self):
            return WeatherReading(
                temperature=20.0,
                humidity=60.0,
                pressure=1006.5, # Queda de 4 hPa
                timestamp="2026-08-23T12:00:00Z"
            )
            
    class MockCSVRepository:
        async def fetch_raw_range(self, start, end):
            # Simulando o df_ref
            return pd.DataFrame([
                {
                    "temperature": 20.0,
                    "humidity": 60.0,
                    "pressure": 1010.5, # Referencia de 3h atras
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=3)
                }
            ])
            
    use_case = GetTrend(MockThingSpeakClient(), MockCSVRepository())
    trend = await use_case.execute()
    
    assert trend.pressure_change_hpa == -4.0
    assert trend.rain_alert is True