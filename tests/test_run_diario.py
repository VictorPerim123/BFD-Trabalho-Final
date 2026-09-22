from app.models.run_diario import RunDiario


def test_segundos_a_partir_de_hhmmss_converte_corretamente():
    assert RunDiario.segundos_a_partir_de_hhmmss("01:02:03") == 3723


def test_segundos_a_partir_de_hhmmss_aceita_formato_mm_ss():
    assert RunDiario.segundos_a_partir_de_hhmmss("05:30") == 330


def test_tempo_formatado_converte_segundos_de_volta_para_hhmmss():
    run = RunDiario(duracao_segundos=3723)
    assert run.tempo_formatado == "01:02:03"


def test_segundos_a_partir_de_hhmmss_rejeita_minutos_ou_segundos_fora_da_faixa():
    import pytest

    with pytest.raises(ValueError):
        RunDiario.segundos_a_partir_de_hhmmss("01:60:00")
    with pytest.raises(ValueError):
        RunDiario.segundos_a_partir_de_hhmmss("01:00:60")


def test_segundos_a_partir_de_hhmmss_rejeita_formato_com_componentes_extras():
    import pytest

    with pytest.raises(ValueError):
        RunDiario.segundos_a_partir_de_hhmmss("1:2:3:4")


def test_segundos_a_partir_de_hhmmss_rejeita_duracao_zero():
    import pytest

    with pytest.raises(ValueError):
        RunDiario.segundos_a_partir_de_hhmmss("00:00:00")


def test_segundos_a_partir_de_hhmmss_aceita_horas_acima_de_24():
    assert RunDiario.segundos_a_partir_de_hhmmss("25:10:05") == 90605
