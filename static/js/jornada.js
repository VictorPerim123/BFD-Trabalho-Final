(function () {
  const gameFilter = document.getElementById("jornada-jogo-filter");
  const contextLabel = document.getElementById("jornada-contexto");
  const tabButtons = document.querySelectorAll("[data-tab]");
  const buildsPanel = document.getElementById("panel-builds");
  const runsPanel = document.getElementById("panel-runs");

  const buildsGrid = document.getElementById("builds-grid");
  const buildsEmpty = document.getElementById("builds-empty");
  const buildAddButton = document.getElementById("btn-add-build");
  const buildCancelButton = document.getElementById("btn-cancel-build-form");
  const buildFormCard = document.getElementById("build-form-card");
  const buildFormTitle = document.getElementById("build-form-title");
  const buildSubmitButton = document.getElementById("build-submit");
  const buildForm = document.getElementById("build-form");
  const buildGameSelect = document.getElementById("build-jogo");

  const runsGrid = document.getElementById("runs-grid");
  const runsEmpty = document.getElementById("runs-empty");
  const runAddButton = document.getElementById("btn-add-run");
  const runCancelButton = document.getElementById("btn-cancel-run-form");
  const runFormCard = document.getElementById("run-form-card");
  const runFormTitle = document.getElementById("run-form-title");
  const runSubmitButton = document.getElementById("run-submit");
  const runForm = document.getElementById("run-form");
  const runGameSelect = document.getElementById("run-jogo");
  const runBuildSelect = document.getElementById("run-build");
  const runCategoryInput = document.getElementById("run-categoria");
  const runDateInput = document.getElementById("run-data");
  const runTimeInput = document.getElementById("run-tempo");
  const runCauseWrapper = document.getElementById("causa-morte-wrapper");
  const runCauseField = document.getElementById("run-causa-morte");
  const runObservationField = document.getElementById("run-observacao");
  const categoryFilter = document.getElementById("run-categoria-filter");
  const resultFilter = document.getElementById("run-resultado-filter");

  let games = [];
  let builds = [];
  let runs = [];
  let gamesById = new Map();
  let buildsById = new Map();
  let editingBuildId = null;
  let editingRunId = null;

  const statusLabels = {
    planejada: "Planejada",
    em_uso: "Em uso",
    finalizada: "Finalizada",
    experimental: "Experimental",
  };

  function selectedGameId() {
    return Number(gameFilter.value) || null;
  }

  function formatDate(iso) {
    if (!iso) return "—";
    const [year, month, day] = iso.split("-");
    return `${day}/${month}/${year}`;
  }

  function todayISO() {
    const now = new Date();
    const offset = now.getTimezoneOffset();
    return new Date(now.getTime() - offset * 60000).toISOString().slice(0, 10);
  }

  function durationIsValid(value) {
    const parts = value.trim().split(":");
    if (![2, 3].includes(parts.length) || parts.some((part) => !/^\d+$/.test(part))) return false;
    const nums = parts.map(Number);
    const hours = parts.length === 3 ? nums[0] : 0;
    const minutes = parts.length === 3 ? nums[1] : nums[0];
    const seconds = parts.length === 3 ? nums[2] : nums[1];
    return hours >= 0 && minutes >= 0 && minutes <= 59 && seconds >= 0 && seconds <= 59 && (hours > 0 || minutes > 0 || seconds > 0);
  }

  function setTab(tab, updateUrl = true) {
    const active = tab === "runs" ? "runs" : "builds";
    buildsPanel.hidden = active !== "builds";
    runsPanel.hidden = active !== "runs";
    tabButtons.forEach((button) => {
      const selected = button.dataset.tab === active;
      button.classList.toggle("is-active", selected);
      button.setAttribute("aria-selected", selected ? "true" : "false");
      button.tabIndex = selected ? 0 : -1;
    });
    if (updateUrl) {
      const url = new URL(window.location.href);
      url.searchParams.set("aba", active);
      history.replaceState(null, "", url);
    }
  }

  function updateUrlGame() {
    const url = new URL(window.location.href);
    if (gameFilter.value) url.searchParams.set("jogo_id", gameFilter.value);
    else url.searchParams.delete("jogo_id");
    history.replaceState(null, "", url);
  }

  function fillGameSelects() {
    const options = games
      .map((game) => `<option value="${game.id}">${SavePointUI.escapeHtml(game.titulo)}</option>`)
      .join("");
    gameFilter.innerHTML = `<option value="">Todos os jogos</option>${options}`;
    buildGameSelect.innerHTML = `<option value="">Selecione um jogo</option>${options}`;
    runGameSelect.innerHTML = `<option value="">Selecione um jogo</option>${options}`;

    const requested = Number(new URLSearchParams(window.location.search).get("jogo_id"));
    if (requested && gamesById.has(requested)) gameFilter.value = String(requested);
  }

  function filteredBuilds() {
    const gameId = selectedGameId();
    return builds.filter((build) => !gameId || build.jogo_id === gameId);
  }

  function filteredRunsBase() {
    const gameId = selectedGameId();
    return runs.filter((run) => !gameId || run.jogo_id === gameId);
  }

  function filteredRuns() {
    return filteredRunsBase().filter((run) => {
      const categoryMatches = !categoryFilter.value || run.categoria === categoryFilter.value;
      const resultMatches = !resultFilter.value || run.resultado === resultFilter.value;
      return categoryMatches && resultMatches;
    });
  }

  function renderSummary() {
    const gameId = selectedGameId();
    const selectedGame = gameId ? gamesById.get(gameId) : null;
    const visibleBuilds = filteredBuilds();
    const visibleRuns = filteredRunsBase();
    document.getElementById("jornada-stat-builds").textContent = visibleBuilds.filter((build) => build.status === "em_uso").length;
    document.getElementById("jornada-stat-runs").textContent = visibleRuns.length;
    document.getElementById("jornada-stat-pbs").textContent = visibleRuns.filter((run) => run.eh_pb).length;
    const latest = visibleRuns.map((run) => run.data).filter(Boolean).sort().reverse()[0];
    document.getElementById("jornada-stat-ultima").textContent = latest ? formatDate(latest) : "—";
    contextLabel.textContent = selectedGame
      ? `Mostrando a jornada de ${selectedGame.titulo}.`
      : "Visão geral de todos os jogos.";
  }

  function attributesToText(attributes) {
    return (attributes || []).map((item) => `${item.nome}: ${item.valor}`).join("\n");
  }

  function parseAttributes(text) {
    const items = [];
    for (const rawLine of text.split("\n")) {
      const line = rawLine.trim();
      if (!line) continue;
      const separator = line.indexOf(":");
      if (separator <= 0 || separator === line.length - 1) {
        throw new Error(`Atributo inválido: "${line}". Use Nome: valor.`);
      }
      items.push({
        nome: line.slice(0, separator).trim(),
        valor: line.slice(separator + 1).trim(),
      });
    }
    return items;
  }

  function renderBuilds() {
    const visible = filteredBuilds();
    buildsGrid.innerHTML = "";
    buildsEmpty.hidden = visible.length > 0;
    visible.forEach((build) => {
      const game = gamesById.get(build.jogo_id);
      const attributes = (build.atributos || [])
        .map((attribute) => `<span class="attribute-chip"><strong>${SavePointUI.escapeHtml(attribute.nome)}</strong> ${SavePointUI.escapeHtml(attribute.valor)}</span>`)
        .join("");
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <div class="game-card__meta">
          <a class="hint" href="/jogos/${build.jogo_id}">${SavePointUI.escapeHtml(game ? game.titulo : "Jogo não encontrado")}</a>
          <span class="badge ${build.status === "em_uso" ? "badge--jogando" : build.status === "finalizada" ? "badge--zerado" : ""}">${SavePointUI.escapeHtml(statusLabels[build.status] || build.status)}</span>
        </div>
        <h3 class="game-card__title">${SavePointUI.escapeHtml(build.nome_build)}</h3>
        ${build.objetivo ? `<p class="hint" style="margin:0;">${SavePointUI.escapeHtml(build.objetivo)}${build.nivel != null ? ` · nível ${build.nivel}` : ""}</p>` : build.nivel != null ? `<p class="hint" style="margin:0;">Nível ${build.nivel}</p>` : ""}
        ${build.descricao ? `<p>${SavePointUI.escapeHtml(build.descricao)}</p>` : ""}
        ${attributes ? `<div class="attribute-list">${attributes}</div>` : ""}
        <div class="build-summary">
          <p><strong>Equipamento</strong><br>${SavePointUI.escapeHtml(build.detalhes_equipamento || "—")}</p>
          <p><strong>Habilidades</strong><br>${SavePointUI.escapeHtml(build.habilidades || "—")}</p>
        </div>
        ${build.observacoes ? `<p class="hint">${SavePointUI.escapeHtml(build.observacoes)}</p>` : ""}
        <div class="game-card__actions">
          <button type="button" class="btn btn-ghost btn-sm" data-action="edit">Editar</button>
          <button type="button" class="btn btn-danger-outline btn-sm" data-action="delete">Excluir build</button>
        </div>`;
      card.querySelector('[data-action="edit"]').addEventListener("click", () => openBuildForm(build));
      card.querySelector('[data-action="delete"]').addEventListener("click", () => deleteBuild(build));
      buildsGrid.appendChild(card);
    });
  }

  function openBuildForm(build = null) {
    setTab("builds");
    editingBuildId = build ? build.id : null;
    buildFormTitle.textContent = build ? `Editar "${build.nome_build}"` : "Nova build";
    buildSubmitButton.textContent = build ? "Salvar alterações" : "Salvar build";
    buildForm.reset();
    buildForm.elements.jogo_id.value = build?.jogo_id || selectedGameId() || "";
    buildForm.elements.nome_build.value = build?.nome_build || "";
    buildForm.elements.status.value = build?.status || "planejada";
    buildForm.elements.nivel.value = build?.nivel ?? "";
    buildForm.elements.objetivo.value = build?.objetivo || "";
    buildForm.elements.descricao.value = build?.descricao || "";
    buildForm.elements.atributos_texto.value = attributesToText(build?.atributos);
    buildForm.elements.detalhes_equipamento.value = build?.detalhes_equipamento || "";
    buildForm.elements.habilidades.value = build?.habilidades || "";
    buildForm.elements.observacoes.value = build?.observacoes || "";
    if (!buildFormCard.open) buildFormCard.showModal();
    buildGameSelect.focus();
  }

  function closeBuildForm() {
    editingBuildId = null;
    buildForm.reset();
    if (buildFormCard.open) buildFormCard.close();
  }

  async function saveBuild(event) {
    event.preventDefault();
    let attributes;
    try {
      attributes = parseAttributes(buildForm.elements.atributos_texto.value);
    } catch (err) {
      SavePointUI.showToast(err.message, { isError: true });
      return;
    }
    const payload = {
      id: editingBuildId,
      jogo_id: Number(buildGameSelect.value),
      nome_build: buildForm.elements.nome_build.value.trim(),
      descricao: buildForm.elements.descricao.value.trim() || null,
      objetivo: buildForm.elements.objetivo.value.trim() || null,
      status: buildForm.elements.status.value,
      nivel: buildForm.elements.nivel.value === "" ? null : Number(buildForm.elements.nivel.value),
      detalhes_equipamento: buildForm.elements.detalhes_equipamento.value.trim() || null,
      habilidades: buildForm.elements.habilidades.value.trim() || null,
      observacoes: buildForm.elements.observacoes.value.trim() || null,
      atributos: attributes,
    };
    if (!payload.jogo_id || !payload.nome_build) {
      SavePointUI.showToast("Selecione o jogo e informe o nome da build.", { isError: true });
      return;
    }
    try {
      await SavePointAPI.saveBuild(payload);
      SavePointUI.showToast(editingBuildId ? "Build atualizada." : "Build salva.");
      closeBuildForm();
      await reloadData();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível salvar a build.", { isError: true });
    }
  }

  async function deleteBuild(build) {
    if (!window.confirm(`Excluir a build "${build.nome_build}"?`)) return;
    try {
      await SavePointAPI.deleteBuild(build.id);
      SavePointUI.showToast("Build excluída.");
      if (editingBuildId === build.id) closeBuildForm();
      await reloadData();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível excluir a build.", { isError: true });
    }
  }

  function updateRunBuildOptions(selected = null) {
    const gameId = Number(runGameSelect.value);
    const options = builds.filter((build) => build.jogo_id === gameId);
    runBuildSelect.innerHTML = '<option value="">Nenhuma build</option>' + options
      .map((build) => `<option value="${build.id}">${SavePointUI.escapeHtml(build.nome_build)}</option>`)
      .join("");
    if (selected && options.some((build) => build.id === Number(selected))) {
      runBuildSelect.value = String(selected);
    }
  }

  function updateRunFilters() {
    const current = categoryFilter.value;
    const categories = [...new Set(filteredRunsBase().map((run) => run.categoria).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, "pt-BR"));
    categoryFilter.innerHTML = '<option value="">Categoria: todas</option>' + categories
      .map((category) => `<option value="${SavePointUI.escapeHtml(category)}">${SavePointUI.escapeHtml(category)}</option>`)
      .join("");
    if (categories.includes(current)) categoryFilter.value = current;
  }

  function renderRuns() {
    updateRunFilters();
    const visible = filteredRuns();
    runsGrid.innerHTML = "";
    runsEmpty.hidden = visible.length > 0;
    visible.forEach((run) => {
      const game = gamesById.get(run.jogo_id);
      const build = run.build_id ? buildsById.get(run.build_id) : null;
      const victory = run.resultado === "vitoria";
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <div class="game-card__meta">
          <div>
            <span class="badge ${victory ? "badge--zerado" : "badge--abandonado"}">${victory ? "Vitória" : "Derrota"}</span>
            ${run.eh_pb ? '<span class="badge badge--platinado">PB</span>' : ""}
          </div>
          <span class="hint">${formatDate(run.data)}</span>
        </div>
        <h3 class="game-card__title"><a href="/jogos/${run.jogo_id}">${SavePointUI.escapeHtml(game ? game.titulo : "Jogo removido")}</a></h3>
        <p class="hint" style="margin:0;">${SavePointUI.escapeHtml(run.categoria || "Casual")}${build ? ` · ${SavePointUI.escapeHtml(build.nome_build)}` : ""}</p>
        <p class="run-time-value">${run.tempo_duracao}</p>
        ${run.causa_morte ? `<p><strong>Causa da morte:</strong> ${SavePointUI.escapeHtml(run.causa_morte)}</p>` : ""}
        ${run.observacao ? `<p class="hint">${SavePointUI.escapeHtml(run.observacao)}</p>` : ""}
        <div class="game-card__actions">
          <button type="button" class="btn btn-ghost btn-sm" data-action="edit">Editar</button>
          <button type="button" class="btn btn-danger-outline btn-sm" data-action="delete">Excluir run</button>
        </div>`;
      card.querySelector('[data-action="edit"]').addEventListener("click", () => openRunForm(run));
      card.querySelector('[data-action="delete"]').addEventListener("click", () => deleteRun(run));
      runsGrid.appendChild(card);
    });
  }

  function toggleRunCause() {
    runCauseWrapper.hidden = runForm.elements.resultado.value !== "derrota";
  }

  function setRunError(id, message) {
    const element = document.getElementById(id);
    if (element) element.textContent = message;
  }

  function openRunForm(run = null) {
    setTab("runs");
    editingRunId = run ? run.id : null;
    runFormTitle.textContent = run ? "Editar run" : "Registrar run";
    runSubmitButton.textContent = run ? "Salvar alterações" : "Salvar run";
    runForm.reset();
    runCategoryInput.value = run?.categoria || "Casual";
    runDateInput.value = run?.data || todayISO();
    runTimeInput.value = run?.tempo_duracao || "";
    runCauseField.value = run?.causa_morte || "";
    runObservationField.value = run?.observacao || "";
    runGameSelect.value = String(run?.jogo_id || selectedGameId() || "");
    updateRunBuildOptions(run?.build_id);
    if (run?.resultado) {
      const result = runForm.querySelector(`input[name="resultado"][value="${run.resultado}"]`);
      if (result) result.checked = true;
    }
    toggleRunCause();
    if (!runFormCard.open) runFormCard.showModal();
    runGameSelect.focus();
  }

  function closeRunForm() {
    editingRunId = null;
    runForm.reset();
    runCategoryInput.value = "Casual";
    runDateInput.value = todayISO();
    if (runFormCard.open) runFormCard.close();
    toggleRunCause();
  }

  function validateRun() {
    let valid = true;
    if (!runGameSelect.value) {
      setRunError("erro-jogo", "Selecione um jogo.");
      valid = false;
    } else setRunError("erro-jogo", "");
    if (!runDateInput.value) {
      setRunError("erro-data", "Informe a data da run.");
      valid = false;
    } else setRunError("erro-data", "");
    if (!runTimeInput.value || !durationIsValid(runTimeInput.value)) {
      setRunError("erro-tempo", "Use HH:MM:SS ou MM:SS com duração maior que zero.");
      valid = false;
    } else setRunError("erro-tempo", "");
    if (!runForm.elements.resultado.value) {
      setRunError("erro-resultado", "Selecione o resultado da run.");
      valid = false;
    } else setRunError("erro-resultado", "");
    if (!runCategoryInput.value.trim()) valid = false;
    return valid;
  }

  async function saveRun(event) {
    event.preventDefault();
    if (!validateRun()) {
      SavePointUI.showToast("Revise os campos da run.", { isError: true });
      return;
    }
    const payload = {
      id: editingRunId,
      jogo_id: Number(runGameSelect.value),
      build_id: runBuildSelect.value ? Number(runBuildSelect.value) : null,
      categoria: runCategoryInput.value.trim(),
      data: runDateInput.value,
      tempo_duracao: runTimeInput.value.trim(),
      resultado: runForm.elements.resultado.value,
      causa_morte: runForm.elements.resultado.value === "derrota" ? runCauseField.value.trim() || null : null,
      observacao: runObservationField.value.trim() || null,
    };
    try {
      const saved = await SavePointAPI.saveRun(payload);
      SavePointUI.showToast(editingRunId ? "Run atualizada." : saved.eh_pb ? "Run salva. Novo recorde pessoal!" : "Run salva.");
      closeRunForm();
      await reloadData();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível salvar a run.", { isError: true });
    }
  }

  async function deleteRun(run) {
    const game = gamesById.get(run.jogo_id);
    if (!window.confirm(`Excluir a run de "${game ? game.titulo : "este jogo"}" de ${formatDate(run.data)}?`)) return;
    try {
      await SavePointAPI.deleteRun(run.id);
      SavePointUI.showToast("Run excluída.");
      if (editingRunId === run.id) closeRunForm();
      await reloadData();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível excluir a run.", { isError: true });
    }
  }

  function renderAll() {
    buildsById = new Map(builds.map((build) => [build.id, build]));
    renderSummary();
    renderBuilds();
    renderRuns();
  }

  async function reloadData() {
    try {
      const [loadedGames, loadedBuilds, loadedRuns] = await Promise.all([
        SavePointAPI.getGames(),
        SavePointAPI.getBuilds(),
        SavePointAPI.getRuns(),
      ]);
      games = loadedGames;
      builds = loadedBuilds;
      runs = loadedRuns;
      gamesById = new Map(games.map((game) => [game.id, game]));
      const currentGame = gameFilter.value;
      fillGameSelects();
      if (currentGame && gamesById.has(Number(currentGame))) gameFilter.value = currentGame;
      renderAll();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível carregar a jornada.", { isError: true });
    }
  }

  function handleInitialAction() {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get("aba") === "runs" ? "runs" : "builds";
    setTab(tab, false);
    const action = params.get("acao");
    const runId = Number(params.get("run_id"));
    if (runId) {
      const run = runs.find((item) => item.id === runId);
      if (run) openRunForm(run);
      return;
    }
    if (action === "nova-run") openRunForm();
    if (action === "nova-build") openBuildForm();
  }

  function closeOnBackdrop(dialog, closeFn) {
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      const rect = dialog.getBoundingClientRect();
      const inside =
        event.clientX >= rect.left &&
        event.clientX <= rect.right &&
        event.clientY >= rect.top &&
        event.clientY <= rect.bottom;
      if (!inside) closeFn();
    }
  });
}

  closeOnBackdrop(buildFormCard, closeBuildForm);
  closeOnBackdrop(runFormCard, closeRunForm);

  tabButtons.forEach((button) => button.addEventListener("click", () => setTab(button.dataset.tab)));
  gameFilter.addEventListener("change", () => {
    updateUrlGame();
    if (buildFormCard.open && !editingBuildId) buildGameSelect.value = gameFilter.value;
    if (runFormCard.open && !editingRunId) {
      runGameSelect.value = gameFilter.value;
      updateRunBuildOptions();
    }
    renderAll();
  });
  categoryFilter.addEventListener("change", renderRuns);
  resultFilter.addEventListener("change", renderRuns);
  document.getElementById("run-filters-form").addEventListener("submit", (event) => event.preventDefault());
  buildAddButton.addEventListener("click", () => openBuildForm());
  buildCancelButton.addEventListener("click", closeBuildForm);
  document.getElementById("btn-cancel-build-form-bottom").addEventListener("click", closeBuildForm);
  buildFormCard.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeBuildForm();
  });
  buildForm.addEventListener("submit", saveBuild);
  runAddButton.addEventListener("click", () => openRunForm());
  runCancelButton.addEventListener("click", closeRunForm);
  document.getElementById("btn-cancel-run-form-bottom").addEventListener("click", closeRunForm);
  runFormCard.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeRunForm();
  });
  runGameSelect.addEventListener("change", () => updateRunBuildOptions());
  runForm.querySelectorAll('input[name="resultado"]').forEach((input) => input.addEventListener("change", toggleRunCause));
  runForm.addEventListener("submit", saveRun);

  reloadData().then(handleInitialAction);
})();
