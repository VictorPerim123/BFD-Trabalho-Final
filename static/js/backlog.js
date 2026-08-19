(function () {
  const grid = document.getElementById("games-grid");
  const emptyState = document.getElementById("empty-state");
  const searchInput = document.getElementById("search-input");
  const statusFilter = document.getElementById("status-filter");
  const categoryFilter = document.getElementById("category-filter");
  const form = document.getElementById("game-form");
  const formCard = document.getElementById("game-form-card");
  const addButton = document.getElementById("btn-add-game");
  const cancelButton = document.getElementById("btn-cancel-form");
  const formTitle = document.getElementById("game-form-title");

  let allGames = [];
  let editingId = null;

  async function loadGames() {
    try {
      allGames = await SavePointAPI.getGames();
      populateCategoryFilter(allGames);
      renderGames();
    } catch (err) {
      SavePointUI.showToast("Não foi possível carregar o backlog agora.", { isError: true });
      console.error(err);
    }
  }

  function populateCategoryFilter(games) {
    const categorias = new Set();
    games.forEach((g) => (g.categorias || []).forEach((c) => categorias.add(c)));
    const current = categoryFilter.value;
    categoryFilter.innerHTML =
      '<option value="">Categoria: todas</option>' +
      [...categorias].sort().map((c) => `<option value="${SavePointUI.escapeHtml(c)}">${SavePointUI.escapeHtml(c)}</option>`).join("");
    categoryFilter.value = current;
  }

  function getFilteredGames() {
    const term = searchInput.value.trim().toLowerCase();
    const status = statusFilter.value;
    const categoria = categoryFilter.value;

    return allGames.filter((g) => {
      const matchesTerm = !term || g.titulo.toLowerCase().includes(term);
      const matchesStatus = !status || g.status === status;
      const matchesCategoria = !categoria || (g.categorias || []).includes(categoria);
      return matchesTerm && matchesStatus && matchesCategoria;
    });
  }

  function renderGames() {
    const games = getFilteredGames();
    grid.innerHTML = "";

    if (games.length === 0) {
      emptyState.hidden = false;
      return;
    }
    emptyState.hidden = true;

    games.forEach((game) => grid.appendChild(renderCard(game)));
  }

  function renderCard(game) {
    const pct = game.total_conquistas
      ? Math.round((game.conquistas_obtidas / game.total_conquistas) * 100)
      : 0;

    const article = document.createElement("article");
    article.className = "game-card";
    article.setAttribute("aria-label", game.titulo);

    article.innerHTML = `
      <div class="game-card__cover" role="img" aria-label="Capa não disponível para ${SavePointUI.escapeHtml(game.titulo)}">
        Sem capa
      </div>
      <h3 class="game-card__title">${SavePointUI.escapeHtml(game.titulo)}</h3>
      <div class="game-card__meta">
        <span class="badge ${SavePointUI.statusBadgeClass(game.status)}">${SavePointUI.statusLabel(game.status)}</span>
        ${game.nota != null ? `<span class="game-card__rating">★ ${game.nota}</span>` : ""}
      </div>
      <div>
        <div class="progress-label">
          <span>Conquistas</span>
          <span>${game.conquistas_obtidas}/${game.total_conquistas} (${pct}%)</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width:${pct}%"></div>
        </div>
      </div>
      <div class="game-card__actions">
        <button type="button" class="btn btn-ghost btn-sm" data-action="edit">Editar</button>
        <a class="btn btn-ghost btn-sm" href="run-form.html?jogo_id=${game.id}&titulo=${encodeURIComponent(game.titulo)}">Nova Run</a>
        <button type="button" class="btn btn-danger-outline btn-sm" data-action="delete">Excluir</button>
      </div>
    `;

    article.querySelector('[data-action="edit"]').addEventListener("click", () => openForm(game));
    article.querySelector('[data-action="delete"]').addEventListener("click", () => handleDelete(game));

    return article;
  }

  function openForm(game) {
    editingId = game ? game.id : null;
    formTitle.textContent = game ? `Editar "${game.titulo}"` : "Adicionar jogo";
    form.elements.titulo.value = game?.titulo || "";
    form.elements.status.value = game?.status || "quero_jogar";
    form.elements.nota.value = game?.nota ?? "";
    form.elements.categorias.value = (game?.categorias || []).join(", ");
    formCard.hidden = false;
    form.elements.titulo.focus();
  }

  function closeForm() {
    formCard.hidden = true;
    form.reset();
    editingId = null;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const titulo = form.elements.titulo.value.trim();
    if (!titulo) {
      SavePointUI.showToast("Informe o título do jogo.", { isError: true });
      return;
    }

    const existing = editingId ? allGames.find((g) => g.id === editingId) : null;
    const payload = {
      id: editingId,
      titulo,
      status: form.elements.status.value,
      nota: form.elements.nota.value ? Number(form.elements.nota.value) : null,
      categorias: form.elements.categorias.value
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean),
      tempo_jogado_horas: existing?.tempo_jogado_horas ?? 0,
      total_conquistas: existing?.total_conquistas ?? 0,
      conquistas_obtidas: existing?.conquistas_obtidas ?? 0,
    };

    await SavePointAPI.saveGame(payload);
    SavePointUI.showToast(editingId ? "Jogo atualizado." : "Jogo adicionado ao backlog.");
    closeForm();
    await loadGames();
  }

  async function handleDelete(game) {
    const confirmed = window.confirm(`Remover "${game.titulo}" do backlog?`);
    if (!confirmed) return;
    await SavePointAPI.deleteGame(game.id);
    SavePointUI.showToast("Jogo removido.");
    await loadGames();
  }

  searchInput.addEventListener("input", renderGames);
  statusFilter.addEventListener("change", renderGames);
  categoryFilter.addEventListener("change", renderGames);
  addButton.addEventListener("click", () => openForm(null));
  cancelButton.addEventListener("click", closeForm);
  form.addEventListener("submit", handleSubmit);

  loadGames();
})();
