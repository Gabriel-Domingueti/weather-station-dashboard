from __future__ import annotations

from datetime import datetime
from typing import Any


def calculate_gd(temp_max: float | None, temp_min: float | None, base_temp: float = 10.2) -> float:
    """
    Graus-Dia pelo método da média (Aparecido & Rolim, 2020).
    Tbase = 10.2°C, conforme Aparecido (2019, Eq. 7), citando Carvalho et al. (2014),
    para o desenvolvimento vegetativo do cafeeiro.
    Nunca retorna negativo (sem acúmulo abaixo da temperatura basal).
    """
    if temp_max is None or temp_min is None:
        return 0.0

    t_mean = (temp_max + temp_min) / 2.0
    gd = t_mean - base_temp

    return max(0.0, gd)


def calculate_dmf_hours(readings: list[tuple[datetime, float]], threshold_pct: float = 90.0) -> float:
    """
    Duração do Molhamento Foliar estimada, em horas, a partir de uma
    lista de leituras (timestamp, umidade_relativa) de um período
    (tipicamente um dia). Soma a duração real entre leituras
    consecutivas em que a umidade ficou >= threshold_pct — não assume
    intervalo fixo entre leituras, calcula pelo delta de tempo real
    entre pontos consecutivos que atendem à condição.
    threshold_pct = 90.0 (UR >= 90%), conforme Sentelhas et al. (2008), calibrado para Piracicaba-SP, Brasil.
    """
    if not readings or len(readings) < 2:
        return 0.0

    readings = sorted(readings, key=lambda x: x[0])

    total_hours = 0.0
    for i in range(1, len(readings)):
        t_prev, h_prev = readings[i - 1]
        t_curr, h_curr = readings[i]

        if h_prev >= threshold_pct and h_curr >= threshold_pct:
            delta_hours = (t_curr - t_prev).total_seconds() / 3600.0
            if delta_hours > 0:
                total_hours += delta_hours

    return total_hours


def estimate_coffee_phenology(gd_acumulado: float, city: str = "varginha") -> dict[str, float]:
    """
    Estima o Número de Nós por ramo plagiotrópico (NN) e o Enfolhamento (LF, %)
    em função do total de Graus-Dia Acumulados desde 1º de setembro,
    utilizando as equações sigmoides calibradas por Aparecido (2019, Cap. 2, Tabela 4, Fig. 4G e 5G)
    para Varginha (Sul de Minas Gerais):
      - NN_VAR: Ymax = 8.16, Ymin = 1.24, X0 = 1498.7, p = 2.23 (R²adj = 0.99)
      - LF_VAR: Ymax = 99.02, Ymin = 34.44, X0 = 3009.8, p = 13.14 (R²adj = 0.99)
    """
    gd_safe = max(1.0, float(gd_acumulado))

    # Crescimento de nós (curva sigmoide crescente: Ymin -> Ymax com ponto de inflexão X0)
    nn_ymin, nn_ymax, nn_x0, nn_p = 1.24, 8.16, 1498.7, 2.23
    nodes = nn_ymin + (nn_ymax - nn_ymin) / (1.0 + ((nn_x0 / gd_safe) ** nn_p))

    # Enfolhamento (curva sigmoide decrescente devido à desfolha após ~2400 GD)
    lf_ymin, lf_ymax, lf_x0, lf_p = 34.44, 99.02, 3009.8, 13.14
    leafiness = lf_ymin + (lf_ymax - lf_ymin) / (1.0 + ((gd_safe / lf_x0) ** lf_p))

    return {
        "nodes_per_branch": round(nodes, 2),
        "leafiness_pct": round(leafiness, 2),
    }


def calculate_phoma_germ_tube_length(temp_c: float) -> float:
    """
    Comprimento estimado do tubo germinativo (µm) de Phoma tarda após 36h de molhamento,
    conforme equação quadrática de Lorenzetti et al. (2015, Figura 6, R² = 0.80):
      y = -42.47 + 18.84*x - 0.52*x²
    Ponto de máximo crescimento em 18.11°C (~128.2 µm).
    """
    t = max(10.0, min(35.0, float(temp_c)))
    length = -42.47 + (18.84 * t) - (0.52 * (t**2))
    return round(max(0.0, length), 2)


def calculate_phoma_audpc(temp_wetness_c: float, wetness_hours_48h: float) -> float:
    """
    Área Abaixo da Curva de Progresso da Doença (AUDPC / AACPD) para Mancha-de-Phoma,
    conforme superfície de resposta de Lorenzetti et al. (2015, Figura 5, R² = 0.71):
      AUDPC = 605.49 - 42.56*t + 2.76*m + 0.79*t² - 0.01*m²
    onde:
      t = temperatura média durante o molhamento (°C), avaliada entre 15 e 30°C
      m = duração do molhamento foliar (horas), avaliada até 48h
    Nota: O polinômio quadrático de Lorenzetti et al. tem vértice local em ~26.9°C,
    mas os próprios autores demonstram (Fig. 5 e 6) que a severidade biológica máxima
    ocorre entre 15 e 20°C combinada com molhamento crescente até 48h, enquanto temperaturas
    >= 25°C reduzem o tubo germinativo em até 60% (Silva et al., 2025).
    """
    t = max(15.0, min(30.0, float(temp_wetness_c)))
    m = max(0.0, min(48.0, float(wetness_hours_48h)))

    if m <= 0.5:
        return 0.0

    raw_audpc = 605.49 - (42.56 * t) + (2.76 * m) + (0.79 * (t**2)) - (0.01 * (m**2))
    # Fator de eficiência germinativa (Lorenzetti et al., 2015 Fig. 6): máximo em 18.11°C
    germ_efficiency = calculate_phoma_germ_tube_length(t) / 128.18
    adjusted_audpc = max(0.0, raw_audpc) * germ_efficiency
    return round(adjusted_audpc, 2)


def _classify_risk_score(score: float) -> tuple[str, str]:
    """Retorna (risk_level, status_label) no padrão de semáforo (Pozza et al., 2021)."""
    if score >= 65.0:
        return "high", "Crítico (Muito Favorável)"
    if score >= 35.0:
        return "moderate", "Atenção (Favorável)"
    return "low", "Baixo (Não Favorável)"


def calculate_coffee_rust_alert(
    temp_avg_15_30d: float,
    temp_max_15_30d: float,
    rh_avg_15_30d: float,
    days_rh_above_80_15_30d: int,
    dmf_avg_hours_7d: float,
    gd_acumulado: float,
) -> dict[str, Any]:
    """
    Avalia o risco e a incidência estimada da Ferrugem do Cafeeiro (Hemileia vastatrix)
    com base em:
      1. Aparecido (2019, Cap. 2 Tabela 8 e Cap. 3 Tabela 4): correlação positiva com Tmax,
         UR média e número de dias com UR >= 80% no período de incubação (10 a 30 dias antes),
         além do modelo regional do Sul de Minas em função de NN, LF e ΣGD.
      2. Pozza et al. (2021): janela de incubação de 15-30 dias antes da incidência (DBRI),
         molhamento foliar crítico >= 6h na faixa térmica de 20 a 25°C, e limiar de ação
         de 5% de incidência (Semáforo Verde < 3%, Amarelo 3-5%, Vermelho >= 5%).
    """
    pheno = estimate_coffee_phenology(gd_acumulado)
    # Modelo regional base do Sul de Minas (Aparecido 2019, Tabela 8):
    # Rust = 22.72 + 7.98*NN - 0.358*LF - 0.00568*ΣGD
    regional_base = (
        22.72
        + (7.98 * pheno["nodes_per_branch"])
        - (0.358 * pheno["leafiness_pct"])
        - (0.00568 * gd_acumulado)
    )
    regional_base = max(0.5, min(35.0, regional_base))

    # Favorabilidade térmica (ótimo entre 20 e 25°C; desfavorável < 15°C ou > 30°C)
    if 20.0 <= temp_avg_15_30d <= 25.0:
        thermal_factor = 1.0
    elif 17.5 <= temp_avg_15_30d < 20.0 or 25.0 < temp_avg_15_30d <= 27.5:
        thermal_factor = 0.65
    elif 15.0 <= temp_avg_15_30d < 17.5 or 27.5 < temp_avg_15_30d <= 30.0:
        thermal_factor = 0.3
    else:
        thermal_factor = 0.05

    # Favorabilidade hídrica / molhamento foliar (mínimo de 6h para infecção segundo Pozza et al., 2021)
    wetness_factor = min(1.0, dmf_avg_hours_7d / 6.0) * 0.65 + min(1.0, days_rh_above_80_15_30d / 10.0) * 0.35
    env_favorability = thermal_factor * wetness_factor

    # Estimativa combinada de incidência (%) para os próximos 15 dias
    # Pondera a curva fenológica regional pela favorabilidade microclimática de infecção (Kushalappa 1983; Pozza 2021)
    estimated_incidence = round(
        (regional_base * 0.45 + 16.0 * env_favorability) * env_favorability,
        2,
    )
    if dmf_avg_hours_7d < 2.5 and days_rh_above_80_15_30d <= 2:
        estimated_incidence = round(min(estimated_incidence, 1.8), 2)

    # Conversão para score (0-100) alinhado ao semáforo de Pozza et al. (2021):
    # < 3% -> Verde (<35), 3 a 5% -> Amarelo (35-65), >= 5% -> Vermelho (>=65)
    if estimated_incidence >= 5.0:
        risk_score = min(100.0, 65.0 + (estimated_incidence - 5.0) * 3.5)
    elif estimated_incidence >= 3.0:
        risk_score = 35.0 + ((estimated_incidence - 3.0) / 2.0) * 30.0
    else:
        risk_score = (estimated_incidence / 3.0) * 34.0

    risk_level, status_label = _classify_risk_score(risk_score)

    return {
        "disease_key": "coffee_rust",
        "name": "Ferrugem do Cafeeiro",
        "scientific_name": "Hemileia vastatrix",
        "risk_level": risk_level,
        "status_label": status_label,
        "risk_score": round(risk_score, 1),
        "estimated_incidence_pct": estimated_incidence,
        "control_threshold_pct": 5.0,
        "favorable_conditions": (
            f"Temp. média {temp_avg_15_30d:.1f}°C (ideal 20–25°C), "
            f"DMF médio {dmf_avg_hours_7d:.1f}h/dia (crítico ≥6h) e "
            f"{days_rh_above_80_15_30d} dias com UR ≥80%."
        ),
        "recommendation": (
            "Alerta vermelho (incidência prevista ≥5% em 15 dias): realizar amostragem imediata no terço médio/inferior e avaliar controle com fungicida protetor/sistêmico (Pozza et al., 2021)."
            if risk_level == "high"
            else (
                "Atenção (incidência estimada entre 3% e 5%): intensificar monitoramento quinzenal das folhas do 3º/4º nó e preparar logística de manejo."
                if risk_level == "moderate"
                else "Condições pouco favoráveis à infecção. Manter monitoramento de rotina sem necessidade de aplicação preventiva fora de época."
            )
        ),
        "references": ["Aparecido (2019)", "Pozza et al. (2021)", "Sentelhas et al. (2008)"],
    }


def calculate_phoma_alert(
    temp_avg_c: float,
    dmf_hours_24h: float,
    dmf_hours_48h: float,
    hours_temp_15_20_7d: float,
    days_rh_above_80_14d: int,
) -> dict[str, Any]:
    """
    Avalia o risco da Mancha-de-Phoma (Phoma tarda) com base em:
      1. Lorenzetti et al. (2015): temperaturas amenas (15 a 20°C) combinadas com períodos
         crescentes de molhamento foliar (6h a 48h, ótimo >36h) maximizam o tubo germinativo
         e a Área Abaixo da Curva de Progresso da Doença (AACPD / AUDPC).
      2. Silva et al. (2025): número de horas entre 15 e 20°C (T15-20), horas com UR >= 80%
         e dias com molhamento foliar (NDLW) permitem prever picos com 2 semanas de antecedência.
    """
    audpc = calculate_phoma_audpc(temp_wetness_c=temp_avg_c, wetness_hours_48h=dmf_hours_48h)
    germ_tube_um = calculate_phoma_germ_tube_length(temp_avg_c)

    # Pontuação por faixa térmica (ótimo: 15 a 20°C)
    if 15.0 <= temp_avg_c <= 20.5:
        temp_score = 40.0
    elif 12.0 <= temp_avg_c < 15.0 or 20.5 < temp_avg_c <= 23.0:
        temp_score = 22.0
    else:
        temp_score = 4.0

    # Pontuação por duração do molhamento foliar em 48h (Lorenzetti et al., 2015: 6h a 48h)
    wetness_score = min(40.0, (dmf_hours_48h / 36.0) * 40.0)

    # Pontuação pelo acúmulo semanal de horas entre 15-20°C e dias úmidos (Silva et al., 2025)
    lag_score = min(12.0, (hours_temp_15_20_7d / 50.0) * 12.0) + min(8.0, (days_rh_above_80_14d / 10.0) * 8.0)

    risk_score = min(100.0, temp_score + wetness_score + lag_score)
    if dmf_hours_48h < 3.0 and days_rh_above_80_14d < 3:
        risk_score = min(risk_score, 25.0)

    estimated_incidence = round(min(35.0, (risk_score / 100.0) * 28.0), 2)
    risk_level, status_label = _classify_risk_score(risk_score)

    return {
        "disease_key": "phoma",
        "name": "Mancha-de-Phoma",
        "scientific_name": "Phoma tarda",
        "risk_level": risk_level,
        "status_label": status_label,
        "risk_score": round(risk_score, 1),
        "estimated_incidence_pct": estimated_incidence,
        "audpc_index": audpc,
        "germ_tube_length_um": germ_tube_um,
        "favorable_conditions": (
            f"Temp. média {temp_avg_c:.1f}°C (ótimo 15–20°C), "
            f"DMF 48h de {dmf_hours_48h:.1f}h (ótimo ≥36h, AACPD={audpc:.0f}) e "
            f"{hours_temp_15_20_7d:.0f}h na faixa 15–20°C nos últimos 7 dias."
        ),
        "recommendation": (
            "Condições ótimas para infecção por Phoma tarda (frio úmido + molhamento prolongado): inspecionar brotações novas, rosetas e avaliar proteção preventiva 2 semanas antes do pico (Silva et al., 2025)."
            if risk_level == "high"
            else (
                "Favorabilidade moderada: monitorar talhões de maior altitude (>900m) e áreas expostas a vento frio e neblina."
                if risk_level == "moderate"
                else "Temperaturas ou molhamento foliar fora da janela crítica de germinação da Phoma."
            )
        ),
        "references": ["Lorenzetti et al. (2015)", "Silva et al. (2025)"],
    }


def calculate_cercospora_alert(
    temp_max_avg_10d: float,
    rh_avg_10d: float,
    dry_days_14d: int,
    gd_acumulado: float,
) -> dict[str, Any]:
    """
    Avalia o risco de Cercosporiose (Cercospora coffeicola) com base em Aparecido (2019):
      1. Equação 12 (Cap. 2, p. 50) para o Sul de Minas:
         %CER_SO = 4.322 + 1.369*NN(ΣGD) - 0.0314*LF(ΣGD) - 0.00213*ΣGD
      2. Correlação positiva e significativa com Temperatura Máxima do ar (Cap. 3, Tabela 5,
         germinação de esporos favorecida em torno de 30°C e excesso de insolação) e
         associação com condições de déficit hídrico / estresse hídrico.
    """
    pheno = estimate_coffee_phenology(gd_acumulado)
    # Equação 12 de Aparecido (2019) calibrada para o Sul de Minas:
    cer_regional = (
        4.322
        + (1.369 * pheno["nodes_per_branch"])
        - (0.0314 * pheno["leafiness_pct"])
        - (0.00213 * gd_acumulado)
    )
    cer_regional = max(1.0, min(15.0, cer_regional))

    # Favorabilidade por Tmax elevada (germinação ótima ~28-30°C)
    if temp_max_avg_10d >= 28.5:
        tmax_score = 45.0
    elif temp_max_avg_10d >= 25.5:
        tmax_score = 28.0
    elif temp_max_avg_10d >= 23.0:
        tmax_score = 15.0
    else:
        tmax_score = 5.0

    # Favorabilidade por estresse hídrico / dias secos + progresso fenológico (ΣGD)
    water_stress_score = min(35.0, (dry_days_14d / 12.0) * 25.0 + max(0.0, (70.0 - rh_avg_10d) * 0.5))
    pheno_score = min(20.0, (cer_regional / 8.0) * 20.0)

    risk_score = min(100.0, tmax_score + water_stress_score + pheno_score)
    estimated_incidence = round(cer_regional * (0.5 + (risk_score / 100.0)), 2)
    risk_level, status_label = _classify_risk_score(risk_score)

    return {
        "disease_key": "cercospora",
        "name": "Cercosporiose (Olho-pardo)",
        "scientific_name": "Cercospora coffeicola",
        "risk_level": risk_level,
        "status_label": status_label,
        "risk_score": round(risk_score, 1),
        "estimated_incidence_pct": estimated_incidence,
        "favorable_conditions": (
            f"Tmax média {temp_max_avg_10d:.1f}°C (germinação favorecida próxima a 30°C), "
            f"{dry_days_14d} dias secos em 14d (UR média {rh_avg_10d:.1f}%) e "
            f"ΣGD = {gd_acumulado:.0f}°C·dia."
        ),
        "recommendation": (
            "Alta favorabilidade (Tmax elevada + déficit hídrico): monitorar folhas do terço médio e frutos em expansão; verificar equilíbrio nutricional (N/K) e necessidade de controle preventivo."
            if risk_level == "high"
            else (
                "Favorabilidade moderada: acompanhar lavouras a pleno sol ou em solos mais arenosos sujeitos a estresse hídrico."
                if risk_level == "moderate"
                else "Baixo risco ambiental para Cercosporiose no momento."
            )
        ),
        "references": ["Aparecido (2019)"],
    }


def calculate_leaf_miner_alert(
    temp_max_avg_10d: float,
    temp_min_avg_10d: float,
    rh_avg_10d: float,
    dry_days_14d: int,
    gd_acumulado: float,
) -> dict[str, Any]:
    """
    Avalia o risco de infestação do Bicho-mineiro (Leucoptera coffeella) com base em Aparecido (2019):
      1. Modelo regional do Sul de Minas (Cap. 2, Tabela 8):
         CLM_SO = 3.854 - 0.459*NN(ΣGD) - 0.017*LF(ΣGD) + 0.00091*ΣGD
      2. Correlação positiva com temperaturas mais elevadas e Tmin no Sul de Minas (Cap. 3, Tabela 6),
         que encurtam o ciclo biológico gerando mais gerações da praga.
      3. Correlação negativa significativa com a precipitação: períodos prolongados de seca
         promovem níveis elevados de infestação no terço superior da planta.
    """
    pheno = estimate_coffee_phenology(gd_acumulado)
    clm_regional = (
        3.854
        - (0.459 * pheno["nodes_per_branch"])
        - (0.017 * pheno["leafiness_pct"])
        + (0.00091 * gd_acumulado)
    )
    clm_regional = max(0.5, min(12.0, clm_regional))

    # Seca prolongada é o principal gatilho populacional do bicho-mineiro
    drought_score = min(50.0, (dry_days_14d / 14.0) * 35.0 + max(0.0, (68.0 - rh_avg_10d) * 0.75))

    # Temperaturas elevadas (Tmax e Tmin) encurtam o ciclo ovo-adulto
    thermal_score = 0.0
    if temp_max_avg_10d >= 27.0:
        thermal_score += min(30.0, (temp_max_avg_10d - 22.0) * 3.8)
    elif temp_max_avg_10d >= 23.5:
        thermal_score += 12.0

    if temp_min_avg_10d >= 15.5:
        thermal_score += min(20.0, (temp_min_avg_10d - 12.0) * 3.0)

    risk_score = min(100.0, drought_score + thermal_score)
    if rh_avg_10d >= 82.0 and dry_days_14d <= 3:
        risk_score = min(risk_score, 20.0)

    estimated_incidence = round(clm_regional * (0.4 + 1.8 * (risk_score / 100.0)), 2)
    risk_level, status_label = _classify_risk_score(risk_score)

    return {
        "disease_key": "leaf_miner",
        "name": "Bicho-mineiro",
        "scientific_name": "Leucoptera coffeella",
        "risk_level": risk_level,
        "status_label": status_label,
        "risk_score": round(risk_score, 1),
        "estimated_incidence_pct": estimated_incidence,
        "favorable_conditions": (
            f"Período seco ({dry_days_14d}/14 dias sem molhamento expressivo, UR média {rh_avg_10d:.1f}%), "
            f"Tmax {temp_max_avg_10d:.1f}°C / Tmin {temp_min_avg_10d:.1f}°C e ΣGD = {gd_acumulado:.0f}°C·dia."
        ),
        "recommendation": (
            "Condições críticas de estiagem e calor (ciclo biológico acelerado): amostrar folhas do terço superior da copa para verificar minas ativas (nível de controle técnico: 20–30% no terço superior)."
            if risk_level == "high"
            else (
                "Favorabilidade moderada ao bicho-mineiro: intensificar inspeção visual nas partes mais altas e ensolaradas da lavoura."
                if risk_level == "moderate"
                else "Período úmido/ameno reduz naturalmente a população adulta de Leucoptera coffeella."
            )
        ),
        "references": ["Aparecido (2019)"],
    }


def evaluate_all_phytosanitary_alerts(
    daily_rows: list[dict[str, Any]],
    raw_readings: list[dict[str, Any]] | None = None,
    region_name: str = "Sul de Minas Gerais (Varginha)",
) -> dict[str, Any]:
    """
    Integra as séries diárias (daily_summary + agrometeorological_indices) e leituras horárias
    recentes para gerar o boletim completo de alertas fitossanitários (Ferrugem, Mancha-de-Phoma,
    Cercosporiose e Bicho-mineiro).
    """
    if not daily_rows:
        return {
            "reference_date": None,
            "region": region_name,
            "gd_acumulado": 0.0,
            "dmf_last_24h": 0.0,
            "dmf_last_48h": 0.0,
            "phenology": {"nodes_per_branch": 0.0, "leafiness_pct": 0.0},
            "alerts": [],
        }

    sorted_days = sorted(daily_rows, key=lambda r: str(r["date"]))
    latest_day = sorted_days[-1]
    ref_date = str(latest_day["date"])
    gd_acum = float(latest_day.get("gd_acumulado") or 0.0)

    last_2 = sorted_days[-2:]
    last_7 = sorted_days[-7:]
    last_10 = sorted_days[-10:]
    last_14 = sorted_days[-14:]
    # Janela de 15 a 30 dias atrás (incubação da ferrugem, Pozza et al. 2021),
    # ou os últimos 15 dias se a série tiver menos de 20 dias
    window_15_30 = sorted_days[-30:-10] if len(sorted_days) >= 20 else sorted_days[-15:]

    def _avg(rows: list[dict[str, Any]], key: str, default: float) -> float:
        vals = [float(r[key]) for r in rows if r.get(key) is not None]
        return sum(vals) / len(vals) if vals else default

    dmf_24h = float(latest_day.get("dmf_hours") or 0.0)
    dmf_48h = sum(float(r.get("dmf_hours") or 0.0) for r in last_2)
    dmf_avg_7d = _avg(last_7, "dmf_hours", dmf_24h)

    temp_avg_recent = _avg(last_2, "temperature_avg", 20.0)
    temp_avg_15_30 = _avg(window_15_30, "temperature_avg", temp_avg_recent)
    temp_max_15_30 = _avg(window_15_30, "temperature_max", 25.0)
    rh_avg_15_30 = _avg(window_15_30, "humidity_avg", 75.0)
    days_rh80_15_30 = sum(1 for r in window_15_30 if float(r.get("humidity_avg") or 0.0) >= 80.0)

    temp_max_10d = _avg(last_10, "temperature_max", 25.0)
    temp_min_10d = _avg(last_10, "temperature_min", 14.0)
    rh_avg_10d = _avg(last_10, "humidity_avg", 70.0)
    days_rh80_14d = sum(1 for r in last_14 if float(r.get("humidity_avg") or 0.0) >= 80.0)
    dry_days_14d = sum(1 for r in last_14 if float(r.get("dmf_hours") or 0.0) < 2.0 and float(r.get("humidity_avg") or 0.0) < 75.0)

    # Contagem de horas entre 15 e 20°C nos últimos 7 dias (Silva et al., 2025)
    if raw_readings:
        hours_15_20_7d = float(
            sum(
                1
                for r in raw_readings
                if r.get("temperature") is not None and 15.0 <= float(r["temperature"]) < 20.0
            )
        )
    else:
        # Estimativa a partir das médias/mínimas diárias quando leituras horárias não são passadas
        hours_15_20_7d = sum(
            8.0 if 14.5 <= float(r.get("temperature_avg") or 20.0) <= 21.0 else 3.0
            for r in last_7
        )

    phenology = estimate_coffee_phenology(gd_acum)

    rust_alert = calculate_coffee_rust_alert(
        temp_avg_15_30d=temp_avg_15_30,
        temp_max_15_30d=temp_max_15_30,
        rh_avg_15_30d=rh_avg_15_30,
        days_rh_above_80_15_30d=days_rh80_15_30,
        dmf_avg_hours_7d=dmf_avg_7d,
        gd_acumulado=gd_acum,
    )
    phoma_alert = calculate_phoma_alert(
        temp_avg_c=temp_avg_recent,
        dmf_hours_24h=dmf_24h,
        dmf_hours_48h=dmf_48h,
        hours_temp_15_20_7d=hours_15_20_7d,
        days_rh_above_80_14d=days_rh80_14d,
    )
    cercospora_alert = calculate_cercospora_alert(
        temp_max_avg_10d=temp_max_10d,
        rh_avg_10d=rh_avg_10d,
        dry_days_14d=dry_days_14d,
        gd_acumulado=gd_acum,
    )
    miner_alert = calculate_leaf_miner_alert(
        temp_max_avg_10d=temp_max_10d,
        temp_min_avg_10d=temp_min_10d,
        rh_avg_10d=rh_avg_10d,
        dry_days_14d=dry_days_14d,
        gd_acumulado=gd_acum,
    )

    return {
        "reference_date": ref_date,
        "region": region_name,
        "gd_acumulado": round(gd_acum, 2),
        "dmf_last_24h": round(dmf_24h, 2),
        "dmf_last_48h": round(dmf_48h, 2),
        "phenology": phenology,
        "alerts": [rust_alert, phoma_alert, cercospora_alert, miner_alert],
    }
