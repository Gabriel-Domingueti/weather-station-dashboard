from datetime import datetime

def calculate_gd(temp_max: float, temp_min: float, base_temp: float = 10.2) -> float:
    """
    Graus-Dia pelo método da média (Aparecido & Rolim, 2020).
    Tbase = 10.2°C, conforme Aparecido (2019, Eq. 7), citando Carvalho et al. (2014), para o desenvolvimento vegetativo do cafeeiro.
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

    # Ensure readings are sorted by timestamp
    readings = sorted(readings, key=lambda x: x[0])
    
    total_hours = 0.0
    for i in range(1, len(readings)):
        t_prev, h_prev = readings[i - 1]
        t_curr, h_curr = readings[i]
        
        # Só soma se ambos os pontos (anterior e atual) estiverem no limiar ou acima
        if h_prev >= threshold_pct and h_curr >= threshold_pct:
            delta_hours = (t_curr - t_prev).total_seconds() / 3600.0
            if delta_hours > 0:
                total_hours += delta_hours
                
    return total_hours
