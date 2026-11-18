import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts import fetch_sul_de_minas_weather as sul_minas


def test_sul_de_minas_cities_catalog():
    """Garante que Varginha e os principais polos cafeeiros do Sul de Minas estão no catálogo."""
    assert "varginha" in sul_minas.SUL_DE_MINAS_CITIES
    varginha = sul_minas.SUL_DE_MINAS_CITIES["varginha"]
    assert varginha["name"] == "Varginha"
    assert -22.0 < varginha["latitude"] < -21.0
    assert -46.0 < varginha["longitude"] < -45.0
    assert varginha["altitude"] == 940

    expected_cities = [
        "varginha",
        "muzambinho",
        "boa_esperanca",
        "carmo_de_minas",
        "tres_pontas",
        "guaxupe",
        "nova_resende",
        "carmo_do_rio_claro",
        "santo_antonio_do_amparo",
        "alfenas",
    ]
    for city_key in expected_cities:
        assert city_key in sul_minas.SUL_DE_MINAS_CITIES


def test_parse_open_meteo_payload():
    """Transforma o JSON horário do Open-Meteo (ECMWF/ERA5) no contrato exato de data/raw (timestamp, temperature, humidity, pressure)."""
    sample_payload = {
        "hourly": {
            "time": [
                "2025-09-01T00:00",
                "2025-09-01T01:00",
                "2025-09-01T02:00",
            ],
            "temperature_2m": [16.4, 15.8, 15.2],
            "relative_humidity_2m": [91.0, 93.5, 95.0],
            "surface_pressure": [914.2, 914.0, 913.8],
        }
    }

    records = sul_minas.parse_open_meteo_records(sample_payload)

    assert len(records) == 3
    assert records[0]["timestamp"].tzinfo is not None
    assert records[0]["temperature"] == 16.4
    assert records[0]["humidity"] == 91.0
    assert records[0]["pressure"] == 914.2


def test_fetch_city_weather_calls_correct_api():
    """Verifica que fetch_city_weather_records consulta a API com as coordenadas de Varginha."""
    captured = {}

    class DummyResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "hourly": {
                    "time": ["2025-10-01T12:00", "2025-10-01T13:00"],
                    "temperature_2m": [22.5, 23.8],
                    "relative_humidity_2m": [72.0, 68.0],
                    "surface_pressure": [915.1, 914.6],
                }
            }

    def fake_get(url, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        return DummyResponse()

    with patch.object(sul_minas.requests, "get", side_effect=fake_get):
        records = sul_minas.fetch_city_weather_records(
            city_key="varginha",
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 2),
        )

    assert "archive-api.open-meteo.com" in captured["url"]
    assert captured["params"]["latitude"] == sul_minas.SUL_DE_MINAS_CITIES["varginha"]["latitude"]
    assert captured["params"]["longitude"] == sul_minas.SUL_DE_MINAS_CITIES["varginha"]["longitude"]
    assert captured["params"]["start_date"] == "2025-10-01"
    assert captured["params"]["end_date"] == "2025-10-02"
    assert len(records) == 2
    assert records[0]["temperature"] == 22.5


def test_write_records_and_rebuild_pipeline():
    """Garante que os dados coletados de Varginha alimentam data/raw, daily_summary.csv e agrometeorological_indices.csv."""
    sample_records = sul_minas.parse_open_meteo_records(
        {
            "hourly": {
                "time": [
                    "2025-09-01T00:00",
                    "2025-09-01T01:00",
                    "2025-09-01T02:00",
                    "2025-09-01T14:00",
                ],
                "temperature_2m": [15.0, 14.5, 14.0, 26.0],
                "relative_humidity_2m": [94.0, 96.0, 92.0, 55.0],
                "surface_pressure": [914.5, 914.2, 914.0, 912.8],
            }
        }
    )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_dir = tmp_path / "data" / "raw"
        agg_dir = tmp_path / "data" / "aggregated"

        sul_minas.write_records_And_rebuild(
            records=sample_records,
            raw_dir=raw_dir,
            aggregated_dir=agg_dir,
        )

        assert (raw_dir / "2025-09.csv").exists()
        assert (agg_dir / "daily_summary.csv").exists()
        assert (agg_dir / "agrometeorological_indices.csv").exists()

        with (agg_dir / "agrometeorological_indices.csv").open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 1
        assert float(rows[0]["dmf_hours"]) == 2.0  # 00:00 -> 01:00 -> 02:00 com UR >= 90%
        assert float(rows[0]["gd"]) == round(((26.0 + 14.0) / 2.0) - 10.2, 2)


class TestFetchSulDeMinas(unittest.TestCase):
    def test_catalog(self):
        test_sul_de_minas_cities_catalog()

    def test_parse(self):
        test_parse_open_meteo_payload()

    def test_fetch_api(self):
        test_fetch_city_weather_calls_correct_api()

    def test_rebuild_pipeline(self):
        test_write_records_and_rebuild_pipeline()


if __name__ == "__main__":
    unittest.main()
