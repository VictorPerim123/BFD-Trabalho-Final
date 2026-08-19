(function () {
  const form = document.getElementById("run-form");
  const gameSelect = document.getElementById("run-jogo");
  const dateInput = document.getElementById("run-data");
  const causaField = document.getElementById("run-causa-morte");
  const causaWrapper = document.getElementById("causa-morte-wrapper");

  function todayISO() {
    const d = new Date();
    return d.toISOString().slice(0, 10);
  }

  async function loadGames() {
    const params = new URLSearchParams(window.location.search);
    const preselectedId = params.get("jogo_id");

    try {
      const games = await SavePointAPI.getGames();
      gameSelect.innerHTML = games
        .map((g) => `<option value="${g.id}">${SavePointUI.escapeHtml(g.titulo)}</option>`)
        .join("");

      if (preselectedId) {
        gameSelect.value = preselectedId;
      }
    } catch (err) {
      SavePointUI.showToast("Não foi possível carregar a lista de jogos.", { isError: true });
      console.error(err);
    }
  }

  function toggleCausaMorte() {
    const resultado = form.elements.resultado.value;
    causaWrapper.hidden = resultado !== "derrota";
  }

  function validate() {
    let valid = true;

    if (!gameSelect.value) {
      setError("erro-jogo", "Selecione um jogo.");
      valid = false;
    } else {
      setError("erro-jogo", "");
    }

    if (!form.elements.tempo.value) {
      setError("erro-tempo", "Informe o tempo de duração da run.");
      valid = false;
    } else {
      setError("erro-tempo", "");
    }

    if (!form.elements.resultado.value) {
      setError("erro-resultado", "Selecione o resultado da run.");
      valid = false;
    } else {
      setError("erro-resultado", "");
    }

    return valid;
  }

  function setError(id, message) {
    const el = document.getElementById(id);
    if (el) el.textContent = message;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validate()) {
      SavePointUI.showToast("Revise os campos destacados.", { isError: true });
      return;
    }

    const payload = {
      jogo_id: Number(gameSelect.value),
      data: dateInput.value,
      tempo_duracao: form.elements.tempo.value,
      resultado: form.elements.resultado.value,
      causa_morte: form.elements.resultado.value === "derrota" ? causaField.value.trim() || null : null,
    };

    await SavePointAPI.saveRun(payload);
    SavePointUI.showToast("Run salva com sucesso!");
    form.reset();
    dateInput.value = todayISO();
    toggleCausaMorte();
    gameSelect.focus();
  }

  form.querySelectorAll('input[name="resultado"]').forEach((input) =>
    input.addEventListener("change", toggleCausaMorte)
  );
  form.addEventListener("submit", handleSubmit);

  dateInput.value = todayISO();
  toggleCausaMorte();
  loadGames();
})();
