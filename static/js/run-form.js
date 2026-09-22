(function () {
  const form = document.getElementById("run-form");
  const gameSelect = document.getElementById("run-jogo");
  const dateInput = document.getElementById("run-data");
  const timeInput = form.elements.tempo;
  const causaField = document.getElementById("run-causa-morte");
  const causaWrapper = document.getElementById("causa-morte-wrapper");
  const pageTitle = document.getElementById("run-page-title");
  const submitButton = document.getElementById("run-submit");

  const params = new URLSearchParams(window.location.search);
  const editingId = Number(params.get("run_id")) || null;
  const preselectedGameId = params.get("jogo_id");

  function todayISO() {
    const d = new Date();
    const ano = d.getFullYear();
    const mes = String(d.getMonth() + 1).padStart(2, "0");
    const dia = String(d.getDate()).padStart(2, "0");
    return `${ano}-${mes}-${dia}`;
  }

  function durationIsValid(value) {
    const parts = value.trim().split(":");
    if (![2, 3].includes(parts.length) || parts.some((part) => !/^\d+$/.test(part))) return false;

    const numbers = parts.map(Number);
    const [hours, minutes, seconds] = parts.length === 2
      ? [0, numbers[0], numbers[1]]
      : numbers;

    if (minutes > 59 || seconds > 59) return false;
    return hours * 3600 + minutes * 60 + seconds > 0;
  }

  async function loadInitialData() {
    try {
      const games = await SavePointAPI.getGames();
      gameSelect.innerHTML = '<option value="">Selecione um jogo</option>' + games
        .map((g) => `<option value="${g.id}">${SavePointUI.escapeHtml(g.titulo)}</option>`)
        .join("");
    } catch (err) {
      SavePointUI.showToast("Não foi possível carregar os jogos.", { isError: true });
      console.error(err);
      return;
    }

    if (editingId) {
      try {
        const run = await SavePointAPI.getRun(editingId);
        pageTitle.textContent = "Editar Run";
        submitButton.textContent = "Salvar alterações";
        gameSelect.value = String(run.jogo_id);
        dateInput.value = run.data;
        timeInput.value = run.tempo_duracao;
        const resultado = form.querySelector(`input[name="resultado"][value="${run.resultado}"]`);
        if (resultado) resultado.checked = true;
        causaField.value = run.causa_morte || "";
      } catch (err) {
        SavePointUI.showToast(err.message || "A run não existe ou não está disponível.", { isError: true });
        window.location.replace("/runs");
        return;
      }
    } else {
      dateInput.value = todayISO();
      if (preselectedGameId) gameSelect.value = preselectedGameId;
    }
    toggleCausaMorte();
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
    } else setError("erro-jogo", "");

    if (!dateInput.value) {
      setError("erro-data", "Informe a data da run.");
      valid = false;
    } else setError("erro-data", "");

    if (!timeInput.value) {
      setError("erro-tempo", "Informe o tempo de duração da run.");
      valid = false;
    } else if (!durationIsValid(timeInput.value)) {
      setError("erro-tempo", "Use HH:MM:SS ou MM:SS com duração maior que zero.");
      valid = false;
    } else setError("erro-tempo", "");

    if (!form.elements.resultado.value) {
      setError("erro-resultado", "Selecione o resultado da run.");
      valid = false;
    } else setError("erro-resultado", "");

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
      id: editingId,
      jogo_id: Number(gameSelect.value),
      data: dateInput.value,
      tempo_duracao: timeInput.value.trim(),
      resultado: form.elements.resultado.value,
      causa_morte: form.elements.resultado.value === "derrota" ? causaField.value.trim() || null : null,
    };

    try {
      await SavePointAPI.saveRun(payload);
      if (editingId) {
        SavePointUI.showToast("Run atualizada com sucesso!");
        window.location.href = "/runs";
        return;
      }
      SavePointUI.showToast("Run salva com sucesso!");
      form.reset();
      dateInput.value = todayISO();
      toggleCausaMorte();
      gameSelect.focus();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível salvar a run.", { isError: true });
    }
  }

  form.querySelectorAll('input[name="resultado"]').forEach((input) =>
    input.addEventListener("change", toggleCausaMorte)
  );
  form.addEventListener("submit", handleSubmit);
  loadInitialData();
})();
