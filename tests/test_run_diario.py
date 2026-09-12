from app.models.run_diario import RunDiario


def test_segundos_a_partir_de_hhmmss_converte_corretamente():
    assert RunDiario.segundos_a_partir_de_hhmmss("01:02:03") == 3723


def test_segundos_a_partir_de_hhmmss_aceita_formato_mm_ss():
    assert RunDiario.segundos_a_partir_de_hhmmss("05:30") == 330


def test_tempo_formatado_converte_segundos_de_volta_para_hhmmss():
    run = RunDiario(duracao_segundos=3723)
    assert run.tempo_formatado == "01:02:03"
