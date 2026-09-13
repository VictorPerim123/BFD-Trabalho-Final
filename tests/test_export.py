def test_exportar_exige_sessao(client):
    resposta = client.get("/backlog/exportar")
    assert resposta.status_code in (301, 302)
    assert "/login" in resposta.headers["Location"]


def test_arquivo_exportado_vem_como_download_e_contem_os_jogos(client_autenticado):
    client_autenticado.post("/api/jogos", json={"titulo": "Hollow Knight", "status": "zerado"})

    resposta = client_autenticado.get("/backlog/exportar")
    assert resposta.status_code == 200
    assert "attachment" in resposta.headers["Content-Disposition"]

    html = resposta.get_data(as_text=True)
    assert "Hollow Knight" in html
    assert "<script src=" not in html
    assert "<link rel=\"stylesheet\"" not in html


def test_titulo_malicioso_nao_fecha_o_bloco_de_script(client_autenticado):
    client_autenticado.post(
        "/api/jogos",
        json={"titulo": "</script><img src=x onerror=alert(1)>", "status": "jogando"},
    )

    html = client_autenticado.get("/backlog/exportar").get_data(as_text=True)

    assert html.count("</script>") == 1
    assert "<\\/script>" in html
