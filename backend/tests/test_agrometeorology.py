import pytest
from datetime import datetime, timedelta
from app.domain.agrometeorology import calculate_gd, calculate_dmf_hours

def test_calculate_gd():
    # Temp media > basal (25 e 15 => media 20. 20 - 10 = 10)
    assert calculate_gd(25.0, 15.0, base_temp=10.0) == 10.0
    
    # Temp media < basal (12 e 4 => media 8. 8 - 10 = -2 => retorna 0)
    assert calculate_gd(12.0, 4.0, base_temp=10.0) == 0.0
    
    # Temp media == basal (12 e 8 => media 10. 10 - 10 = 0 => retorna 0)
    assert calculate_gd(12.0, 8.0, base_temp=10.0) == 0.0

def test_calculate_dmf_hours():
    t0 = datetime(2026, 8, 1, 10, 0, 0)
    
    # Lista vazia -> 0
    assert calculate_dmf_hours([], threshold_pct=90.0) == 0.0

    # Sequencia toda acima do limiar
    # Leituras espaçadas irregularmente
    readings_all_above = [
        (t0, 95.0),
        (t0 + timedelta(hours=1), 92.0), # delta 1h
        (t0 + timedelta(hours=1, minutes=30), 91.0) # delta 0.5h
    ]
    # Esperado: 1h + 0.5h = 1.5h
    assert calculate_dmf_hours(readings_all_above, threshold_pct=90.0) == 1.5

    # Leituras que cruzam o limiar no meio
    readings_mixed = [
        (t0, 85.0),                               # < limiar, não soma anterior (inexistente) e nem próximo
        (t0 + timedelta(hours=1), 95.0),          # >= limiar, inicia trecho se proximo for tb, ou se anterior for
        # Espera, como funciona? "Soma a duração real entre leituras consecutivas em que a umidade ficou >= threshold_pct"
        # Isso significa que ambas (anterior e atual) devem ser >= threshold_pct para somar o delta entre elas.
        (t0 + timedelta(hours=2), 92.0),          # >= limiar (delta 1h somado)
        (t0 + timedelta(hours=3), 88.0),          # < limiar (delta 1h nao somado)
        (t0 + timedelta(hours=4), 91.0),          # >= limiar
        (t0 + timedelta(hours=6), 95.0),          # >= limiar (delta 2h somado)
    ]
    # Esperado: (t2-t1) = 1h, e (t5-t4) = 2h. Total = 3h.
    assert calculate_dmf_hours(readings_mixed, threshold_pct=90.0) == 3.0

    # Apenas um ponto >= limiar (não tem par consecutivo para gerar delta)
    readings_single_above = [
        (t0, 85.0),
        (t0 + timedelta(hours=1), 95.0),
        (t0 + timedelta(hours=2), 85.0),
    ]
    assert calculate_dmf_hours(readings_single_above, threshold_pct=90.0) == 0.0
