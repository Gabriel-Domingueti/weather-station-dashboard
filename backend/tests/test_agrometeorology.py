import unittest
from datetime import datetime, timedelta

try:
    import pytest
except ImportError:
    pytest = None

from app.domain.agrometeorology import (
    calculate_cercospora_alert,
    calculate_coffee_rust_alert,
    calculate_dmf_hours,
    calculate_gd,
    calculate_leaf_miner_alert,
    calculate_phoma_alert,
    calculate_phoma_audpc,
    calculate_phoma_germ_tube_length,
    estimate_coffee_phenology,
    evaluate_all_phytosanitary_alerts,
)


def test_calculate_gd():
    # Temp media > basal (25 e 15 => media 20. 20 - 10.2 = 9.8)
    assert calculate_gd(25.0, 15.0) == 9.8

    # Temp media < basal (12 e 4 => media 8. 8 - 10.2 = -2.2 => retorna 0)
    assert calculate_gd(12.0, 4.0) == 0.0

    # Temp media == basal (12 e 8 => media 10. 10 - 10.2 = -0.2 => retorna 0)
    assert calculate_gd(12.0, 8.0) == 0.0


def test_calculate_dmf_hours():
    t0 = datetime(2026, 8, 1, 10, 0, 0)

    # Lista vazia -> 0
    assert calculate_dmf_hours([], threshold_pct=90.0) == 0.0

    # Sequencia toda acima do limiar
    readings_all_above = [
        (t0, 95.0),
        (t0 + timedelta(hours=1), 92.0),  # delta 1h
        (t0 + timedelta(hours=1, minutes=30), 91.0),  # delta 0.5h
    ]
    assert calculate_dmf_hours(readings_all_above, threshold_pct=90.0) == 1.5

    # Leituras que cruzam o limiar no meio
    readings_mixed = [
        (t0, 85.0),
        (t0 + timedelta(hours=1), 95.0),
        (t0 + timedelta(hours=2), 92.0),  # +1h
        (t0 + timedelta(hours=3), 88.0),
        (t0 + timedelta(hours=4), 91.0),
        (t0 + timedelta(hours=6), 95.0),  # +2h
    ]
    assert calculate_dmf_hours(readings_mixed, threshold_pct=90.0) == 3.0

    # Apenas um ponto >= limiar (não tem par consecutivo para gerar delta)
    readings_single_above = [
        (t0, 85.0),
        (t0 + timedelta(hours=1), 95.0),
        (t0 + timedelta(hours=2), 85.0),
    ]
    assert calculate_dmf_hours(readings_single_above, threshold_pct=90.0) == 0.0


def test_estimate_coffee_phenology_varginha():
    """
    Testa as equações de crescimento de nós (NN) e enfolhamento (LF)
    em função de Graus-Dia Acumulados para Varginha (Aparecido 2019, Tabela 4).
    """
    pheno_start = estimate_coffee_phenology(gd_acumulado=100.0)
    pheno_mid = estimate_coffee_phenology(gd_acumulado=1500.0)
    pheno_late = estimate_coffee_phenology(gd_acumulado=3200.0)

    # O número de nós por ramo cresce com GD acumulado (de ~1.24 até ~8.16 em Varginha)
    assert pheno_start["nodes_per_branch"] < pheno_mid["nodes_per_branch"] < pheno_late["nodes_per_branch"]
    assert 1.2 <= pheno_start["nodes_per_branch"] <= 2.0
    assert 4.0 <= pheno_mid["nodes_per_branch"] <= 5.5

    # O enfolhamento (%) começa alto (~99%) e reduz após 2400 GD devido à desfolha
    assert pheno_start["leafiness_pct"] > pheno_late["leafiness_pct"]
    assert pheno_start["leafiness_pct"] > 95.0
    assert pheno_late["leafiness_pct"] < 65.0


def test_phoma_lorenzetti_equations():
    """
    Testa as equações de Lorenzetti et al. (2015) para Phoma tarda:
    1) Tubo germinativo (Fig. 6): máximo em ~18.11°C, queda acentuada em 30°C.
    2) AUDPC (Fig. 5): aumenta com molhamento até 48h e temperaturas entre 15-20°C.
    """
    tube_18c = calculate_phoma_germ_tube_length(18.1)
    tube_30c = calculate_phoma_germ_tube_length(30.0)
    assert tube_18c > 120.0
    assert tube_30c < 60.0
    assert tube_18c > tube_30c * 2.0

    # AUDPC em 18°C com 48h de molhamento deve ser muito maior que em 28°C com 6h
    audpc_favorable = calculate_phoma_audpc(temp_wetness_c=18.0, wetness_hours_48h=40.0)
    audpc_unfavorable = calculate_phoma_audpc(temp_wetness_c=28.0, wetness_hours_48h=4.0)
    assert audpc_favorable > audpc_unfavorable
    assert audpc_favorable > 180.0


def test_calculate_phoma_alert_levels():
    """
    Verifica o alerta de Mancha-de-Phoma (Lorenzetti et al. 2015; Silva et al. 2025):
    - Temperatura entre 15 e 20°C + molhamento foliar elevado -> HIGH (vermelho)
    - Temperatura alta (>26°C) e sem molhamento -> LOW (verde)
    """
    high_alert = calculate_phoma_alert(
        temp_avg_c=17.5,
        dmf_hours_24h=12.0,
        dmf_hours_48h=36.0,
        hours_temp_15_20_7d=65.0,
        days_rh_above_80_14d=11,
    )
    assert high_alert["risk_level"] == "high"
    assert high_alert["disease_key"] == "phoma"
    assert high_alert["risk_score"] >= 70.0

    low_alert = calculate_phoma_alert(
        temp_avg_c=27.0,
        dmf_hours_24h=0.0,
        dmf_hours_48h=1.0,
        hours_temp_15_20_7d=4.0,
        days_rh_above_80_14d=1,
    )
    assert low_alert["risk_level"] == "low"
    assert low_alert["risk_score"] < 35.0


def test_calculate_coffee_rust_alert_levels():
    """
    Verifica o alerta de Ferrugem (Hemileia vastatrix - Aparecido 2019; Pozza et al. 2021):
    - Temperatura 20-25°C, DMF >= 6h, alta umidade nos últimos 15-30 dias -> HIGH
    - Clima frio/seco sem molhamento foliar -> LOW
    """
    high_rust = calculate_coffee_rust_alert(
        temp_avg_15_30d=22.4,
        temp_max_15_30d=26.5,
        rh_avg_15_30d=84.0,
        days_rh_above_80_15_30d=13,
        dmf_avg_hours_7d=8.5,
        gd_acumulado=1850.0,
    )
    assert high_rust["risk_level"] == "high"
    assert high_rust["disease_key"] == "coffee_rust"
    assert high_rust["estimated_incidence_pct"] >= 5.0  # Limiar de 5% de Pozza et al. (2021)

    low_rust = calculate_coffee_rust_alert(
        temp_avg_15_30d=14.0,
        temp_max_15_30d=19.0,
        rh_avg_15_30d=52.0,
        days_rh_above_80_15_30d=0,
        dmf_avg_hours_7d=0.5,
        gd_acumulado=300.0,
    )
    assert low_rust["risk_level"] == "low"


def test_calculate_cercospora_and_leaf_miner_alerts():
    """
    Verifica Cercosporiose e Bicho-mineiro (Aparecido 2019):
    Ambos são favorecidos por temperaturas elevadas (Tmax alta ~29-31°C)
    e períodos secos (baixa umidade / déficit hídrico).
    """
    hot_dry_cercospora = calculate_cercospora_alert(
        temp_max_avg_10d=30.2,
        rh_avg_10d=52.0,
        dry_days_14d=13,
        gd_acumulado=1600.0,
    )
    assert hot_dry_cercospora["risk_level"] in ("moderate", "high")
    assert hot_dry_cercospora["risk_score"] >= 55.0

    hot_dry_miner = calculate_leaf_miner_alert(
        temp_max_avg_10d=30.5,
        temp_min_avg_10d=18.5,
        rh_avg_10d=48.0,
        dry_days_14d=14,
        gd_acumulado=1900.0,
    )
    assert hot_dry_miner["risk_level"] == "high"
    assert hot_dry_miner["risk_score"] >= 70.0

    cool_wet_miner = calculate_leaf_miner_alert(
        temp_max_avg_10d=20.0,
        temp_min_avg_10d=12.0,
        rh_avg_10d=88.0,
        dry_days_14d=1,
        gd_acumulado=600.0,
    )
    assert cool_wet_miner["risk_level"] == "low"


def test_evaluate_all_phytosanitary_alerts():
    """Verifica a agregação completa dos 4 alertas fitossanitários para o dashboard."""
    daily_rows = []
    base_dt = datetime(2026, 10, 1)
    for i in range(30):
        d_str = (base_dt + timedelta(days=i)).strftime("%Y-%m-%d")
        daily_rows.append(
            {
                "date": d_str,
                "temperature_avg": 21.8,
                "temperature_min": 16.5,
                "temperature_max": 26.2,
                "humidity_avg": 82.5,
                "humidity_min": 62.0,
                "humidity_max": 96.0,
                "pressure_avg": 906.0,
                "gd": 11.15,
                "gd_acumulado": 300.0 + i * 11.15,
                "dmf_hours": 7.5,
            }
        )

    report = evaluate_all_phytosanitary_alerts(daily_rows=daily_rows, raw_readings=[])
    assert report["region"] == "Sul de Minas Gerais (Varginha)"
    assert len(report["alerts"]) == 4
    keys = [a["disease_key"] for a in report["alerts"]]
    assert keys == ["coffee_rust", "phoma", "cercospora", "leaf_miner"]


class TestAgrometeorologySuite(unittest.TestCase):
    def test_gd(self):
        test_calculate_gd()

    def test_dmf(self):
        test_calculate_dmf_hours()

    def test_phenology(self):
        test_estimate_coffee_phenology_varginha()

    def test_phoma_equations(self):
        test_phoma_lorenzetti_equations()

    def test_phoma_alert(self):
        test_calculate_phoma_alert_levels()

    def test_rust_alert(self):
        test_calculate_coffee_rust_alert_levels()

    def test_cercospora_and_miner(self):
        test_calculate_cercospora_and_leaf_miner_alerts()

    def test_evaluate_all(self):
        test_evaluate_all_phytosanitary_alerts()


if __name__ == "__main__":
    unittest.main()
