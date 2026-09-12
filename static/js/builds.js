(function () {
  const grid = document.getElementById("builds-grid");
  const emptyState = document.getElementById("empty-state");

  const addButton = document.getElementById("btn-add-build");
  const cancelButton = document.getElementById("btn-cancel-build-form");
  const formCard = document.getElementById("build-form-card");
  const form = document.getElementById("build-form");
  const gameSelect = document.getElementById("build-jogo");

  let gamesById = new Map();

  async function loadBuilds() {
    try {
      const [builds, games] = await Promise.all([
        SavePointAPI.getBuilds(),
        SavePointAPI.getGames(),
      ]);
      gamesById = new Map(games.map((g) => [g.id, g]));
      populateGameSelect(games);
      render(builds, gamesById);
    } catch (err) {
      SavePointUI.showToast("Não foi possível carregar as builds.", { isError: true });
      console.error(err);
    }
  }

  function populateGameSelect(games) {
    gameSelect.innerHTML = games
      .map((g) => `<option value="${g.id}">${SavePointUI.escapeHtml(g.titulo)}</option>`)
      .join("");
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
          <button type="button" class="btn btn-danger-outline btn-sm" data-action="delete">Excluir build</button>
        </div>
      `;
      card
        .querySelector('[data-action="delete"]')
        .addEventListener("click", () => handleDelete(build));
      grid.appendChild(card);
    });
  }

  async function handleDelete(build) {
    const confirmado = window.confirm(`Excluir a build "${build.nome_build}"?`);
    if (!confirmado) return;
    try {
      await SavePointAPI.deleteBuild(build.id);
      SavePointUI.showToast("Build excluída.");
      await loadBuilds();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível excluir a build.", { isError: true });
    }
  }

  function openForm() {
    formCard.hidden = false;
    gameSelect.focus();
  }

  function closeForm() {
    formCard.hidden = true;
    form.reset();
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const payload = {
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
      SavePointUI.showToast("Build salva.");
      closeForm();
      await loadBuilds();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível salvar a build.", { isError: true });
    }
  }

  addButton.addEventListener("click", openForm);
  cancelButton.addEventListener("click", closeForm);
  form.addEventListener("submit", handleSubmit);

  loadBuilds();
})();
