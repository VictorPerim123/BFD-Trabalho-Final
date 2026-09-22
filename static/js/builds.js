(function () {
  const grid = document.getElementById("builds-grid");
  const emptyState = document.getElementById("empty-state");
  const addButton = document.getElementById("btn-add-build");
  const cancelButton = document.getElementById("btn-cancel-build-form");
  const formCard = document.getElementById("build-form-card");
  const formTitle = document.getElementById("build-form-title");
  const submitButton = document.getElementById("build-submit");
  const form = document.getElementById("build-form");
  const gameSelect = document.getElementById("build-jogo");

  let gamesById = new Map();
  let allBuilds = [];
  let editingId = null;

  async function loadBuilds() {
    try {
      const [builds, games] = await Promise.all([
        SavePointAPI.getBuilds(),
        SavePointAPI.getGames(),
      ]);
      allBuilds = builds;
      gamesById = new Map(games.map((g) => [g.id, g]));
      populateGameSelect(games);
      render(builds, gamesById);
    } catch (err) {
      SavePointUI.showToast("Não foi possível carregar as builds.", { isError: true });
      console.error(err);
    }
  }

  function populateGameSelect(games) {
    const atual = gameSelect.value;
    gameSelect.innerHTML = '<option value="">Selecione um jogo</option>' + games
      .map((g) => `<option value="${g.id}">${SavePointUI.escapeHtml(g.titulo)}</option>`)
      .join("");
    if (atual) gameSelect.value = atual;
  }

  function render(builds, gamesMap) {
    grid.innerHTML = "";
    if (builds.length === 0) {
      emptyState.hidden = false;
      return;
    }
    emptyState.hidden = true;

    builds.forEach((build) => {
      const jogo = gamesMap.get(build.jogo_id);
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <p class="hint" style="margin-bottom:0.25rem;">${SavePointUI.escapeHtml(jogo ? jogo.titulo : "Jogo não encontrado")}</p>
        <h3 style="margin-bottom:0.5rem;">${SavePointUI.escapeHtml(build.nome_build)}</h3>
        <p><strong>Equipamento:</strong> ${SavePointUI.escapeHtml(build.detalhes_equipamento || "—")}</p>
        <p style="margin-bottom:0;"><strong>Habilidades:</strong> ${SavePointUI.escapeHtml(build.habilidades || "—")}</p>
        <div class="game-card__actions">
          <button type="button" class="btn btn-ghost btn-sm" data-action="edit">Editar</button>
          <button type="button" class="btn btn-danger-outline btn-sm" data-action="delete">Excluir build</button>
        </div>
      `;
      card.querySelector('[data-action="edit"]').addEventListener("click", () => openForm(build));
      card.querySelector('[data-action="delete"]').addEventListener("click", () => handleDelete(build));
      grid.appendChild(card);
    });
  }

  async function handleDelete(build) {
    const confirmado = window.confirm(`Excluir a build "${build.nome_build}"?`);
    if (!confirmado) return;
    try {
      await SavePointAPI.deleteBuild(build.id);
      SavePointUI.showToast("Build excluída.");
      if (editingId === build.id) closeForm();
      await loadBuilds();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível excluir a build.", { isError: true });
    }
  }

  function openForm(build = null) {
    editingId = build ? build.id : null;
    formTitle.textContent = build ? `Editar "${build.nome_build}"` : "Nova anotação de build";
    submitButton.textContent = build ? "Salvar alterações" : "Salvar";
    form.elements.jogo_id.value = build?.jogo_id || "";
    form.elements.nome_build.value = build?.nome_build || "";
    form.elements.detalhes_equipamento.value = build?.detalhes_equipamento || "";
    form.elements.habilidades.value = build?.habilidades || "";
    formCard.hidden = false;
    gameSelect.focus();
  }

  function closeForm() {
    formCard.hidden = true;
    form.reset();
    editingId = null;
    formTitle.textContent = "Nova anotação de build";
    submitButton.textContent = "Salvar";
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const payload = {
      id: editingId,
      jogo_id: Number(gameSelect.value),
      nome_build: form.elements.nome_build.value.trim(),
      detalhes_equipamento: form.elements.detalhes_equipamento.value.trim(),
      habilidades: form.elements.habilidades.value.trim(),
    };

    if (!payload.jogo_id || !payload.nome_build) {
      SavePointUI.showToast("Selecione o jogo e informe o nome da build.", { isError: true });
      return;
    }

    try {
      await SavePointAPI.saveBuild(payload);
      SavePointUI.showToast(editingId ? "Build atualizada." : "Build salva.");
      closeForm();
      await loadBuilds();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível salvar a build.", { isError: true });
    }
  }

  addButton.addEventListener("click", () => openForm(null));
  cancelButton.addEventListener("click", closeForm);
  form.addEventListener("submit", handleSubmit);
  loadBuilds();
})();
