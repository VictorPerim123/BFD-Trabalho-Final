(function () {
  const grid = document.getElementById("games-grid");
  const emptyState = document.getElementById("empty-state");
  const pagination = document.getElementById("pagination");
  const summary = document.getElementById("backlog-summary");
  const searchInput = document.getElementById("search-input");
  const statusFilter = document.getElementById("status-filter");
  const categoryFilter = document.getElementById("category-filter");
  const priorityFilter = document.getElementById("priority-filter");
  const originFilter = document.getElementById("origin-filter");
  const sortFilter = document.getElementById("sort-filter");
  const favoriteFilter = document.getElementById("favorite-filter");
  const achievementsFilter = document.getElementById("achievements-filter");
  const clearFiltersButton = document.getElementById("btn-clear-filters");
  const form = document.getElementById("game-form");
  const formCard = document.getElementById("game-form-card");
  const addButton = document.getElementById("btn-add-game");
  const cancelButton = document.getElementById("btn-cancel-form");
  const closeButton = document.getElementById("btn-close-game-form");
  const formTitle = document.getElementById("game-form-title");

  let currentGames = [];
  let currentPage = 1;
  let editingId = null;
  let searchTimer = null;

  function readUrlState() {
    const params = new URLSearchParams(window.location.search);
    searchInput.value = params.get("q") || "";
    statusFilter.value = params.get("status") || "";
    priorityFilter.value = params.get("prioridade") || "";
    originFilter.value = params.get("origem") || "";
    sortFilter.value = params.get("ordenar") || "titulo_asc";
    favoriteFilter.checked = params.get("favorito") === "true";
    achievementsFilter.checked = params.get("com_conquistas") === "true";
    currentPage = Math.max(1, Number(params.get("page")) || 1);
    return params.get("categoria") || "";
  }

  let pendingInitialCategory = readUrlState();
  const requestedEditId = Number(new URLSearchParams(window.location.search).get("editar"));

  function buildParams(page = currentPage) {
    const params = {
      page: String(page),
      per_page: "24",
      ordenar: sortFilter.value || "titulo_asc",
    };
    if (searchInput.value.trim()) params.q = searchInput.value.trim();
    if (statusFilter.value) params.status = statusFilter.value;
    if (categoryFilter.value) params.categoria = categoryFilter.value;
    if (priorityFilter.value) params.prioridade = priorityFilter.value;
    if (originFilter.value) params.origem = originFilter.value;
    if (favoriteFilter.checked) params.favorito = "true";
    if (achievementsFilter.checked) params.com_conquistas = "true";
    return params;
  }

  function syncUrl(params) {
    const query = new URLSearchParams(params);
    if (query.get("page") === "1") query.delete("page");
    if (query.get("ordenar") === "titulo_asc") query.delete("ordenar");
    query.delete("per_page");
    const next = query.toString();
    history.replaceState(null, "", next ? `${location.pathname}?${next}` : location.pathname);
  }

  async function loadGames(page = currentPage) {
    const params = buildParams(page);
    try {
      const data = await SavePointAPI.getGamesPage(params);
      currentGames = data.itens || [];
      currentPage = data.paginacao?.pagina || 1;
      populateCategoryFilter(data.filtros?.categorias || []);
      renderGames();
      renderPagination(data.paginacao || {});
      renderSummary(data.paginacao || {});
      syncUrl(buildParams(currentPage));
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível carregar o backlog agora.", { isError: true });
      console.error(err);
    }
  }

  function populateCategoryFilter(categorias) {
    const current = categoryFilter.value || pendingInitialCategory;
    categoryFilter.innerHTML = '<option value="">Categoria: todas</option>';
    categorias.forEach((categoria) => {
      const option = document.createElement("option");
      option.value = categoria;
      option.textContent = categoria;
      categoryFilter.appendChild(option);
    });
    categoryFilter.value = [...categoryFilter.options].some((option) => option.value === current) ? current : "";
    pendingInitialCategory = "";
  }

  function renderSummary(meta) {
    const total = meta.total || 0;
    const paginas = meta.paginas || 0;
    summary.textContent = total === 1
      ? "1 jogo encontrado"
      : `${total} jogos encontrados${paginas > 1 ? ` · página ${meta.pagina} de ${paginas}` : ""}`;
  }

  function renderGames() {
    grid.innerHTML = "";
    emptyState.hidden = currentGames.length !== 0;
    currentGames.forEach((game) => grid.appendChild(renderCard(game)));
  }

  function renderCard(game) {
    const pct = game.percentual_conquistas || 0;
    const article = document.createElement("article");
    article.className = "game-card";
    article.setAttribute("aria-label", game.titulo);

    article.innerHTML = `
      <div class="game-card__cover" role="img" aria-label="Capa de ${SavePointUI.escapeHtml(game.titulo)}">
        <span class="cover-placeholder">Sem capa</span>
      </div>
      <div class="game-card__headline">
        <h3 class="game-card__title"><a href="/jogos/${game.id}">${SavePointUI.escapeHtml(game.titulo)}</a></h3>
        <button type="button" class="favorite-button${game.favorito ? " is-active" : ""}" data-action="favorite" aria-label="${game.favorito ? "Remover dos favoritos" : "Adicionar aos favoritos"}" aria-pressed="${game.favorito ? "true" : "false"}">★</button>
      </div>
      <p class="game-card__playtime">${SavePointUI.formatHoras(game.tempo_jogado_horas)} jogadas${game.steam_appid ? " · Steam" : " · Manual"}</p>
      <div class="game-card__meta">
        <span class="badge ${SavePointUI.statusBadgeClass(game.status)}">${SavePointUI.statusLabel(game.status)}</span>
        ${game.nota != null ? `<span class="game-card__rating">★ ${game.nota}</span>` : ""}
      </div>
      <label class="priority-control">
        <span>Prioridade</span>
        <select data-action="priority" aria-label="Prioridade de ${SavePointUI.escapeHtml(game.titulo)}">
          <option value="baixa"${game.prioridade === "baixa" ? " selected" : ""}>Baixa</option>
          <option value="normal"${game.prioridade === "normal" ? " selected" : ""}>Normal</option>
          <option value="alta"${game.prioridade === "alta" ? " selected" : ""}>Alta</option>
        </select>
      </label>
      <div>
        <div class="progress-label">
          <span>Conquistas</span>
          <span>${game.conquistas_obtidas}/${game.total_conquistas} (${pct}%)</span>
        </div>
        <div class="progress-track" aria-label="${pct}% das conquistas">
          <div class="progress-fill" style="width:${pct}%"></div>
        </div>
      </div>
      <div class="game-card__actions">
        <a class="btn btn-ghost btn-sm" href="/jogos/${game.id}">Detalhes</a>
        <button type="button" class="btn btn-ghost btn-sm" data-action="edit">Editar</button>
        <button type="button" class="btn btn-danger-outline btn-sm" data-action="delete">Excluir</button>
      </div>
    `;

    loadCover(article.querySelector(".game-card__cover"), game);
    article.querySelector('[data-action="favorite"]').addEventListener("click", () => toggleFavorite(game));
    article.querySelector('[data-action="priority"]').addEventListener("change", (event) => updatePriority(game, event.target.value));
    article.querySelector('[data-action="edit"]').addEventListener("click", () => openForm(game));
    article.querySelector('[data-action="delete"]').addEventListener("click", () => handleDelete(game));
    return article;
  }

  function loadCover(cover, game) {
    if (!game.capa_url) return;
    const placeholder = cover.querySelector(".cover-placeholder");
    const image = document.createElement("img");
    image.alt = `Capa de ${game.titulo}`;
    image.loading = "lazy";
    image.decoding = "async";
    image.referrerPolicy = "no-referrer";
    image.addEventListener("load", () => {
      if (placeholder) placeholder.remove();
    }, { once: true });
    image.addEventListener("error", () => {
      image.remove();
      cover.setAttribute("aria-label", `Capa não disponível para ${game.titulo}`);
    }, { once: true });
    cover.appendChild(image);
    image.src = game.capa_url;
  }

  async function toggleFavorite(game) {
    try {
      await SavePointAPI.updateGamePreferences(game.id, { favorito: !game.favorito });
      await loadGames(currentPage);
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível alterar o favorito.", { isError: true });
    }
  }

  async function updatePriority(game, prioridade) {
    try {
      await SavePointAPI.updateGamePreferences(game.id, { prioridade });
      if (sortFilter.value === "prioridade" || priorityFilter.value) await loadGames(currentPage);
      else game.prioridade = prioridade;
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível alterar a prioridade.", { isError: true });
      await loadGames(currentPage);
    }
  }

  function renderPagination(meta) {
    pagination.innerHTML = "";
    const pages = meta.paginas || 0;
    if (pages <= 1) {
      pagination.hidden = true;
      return;
    }
    pagination.hidden = false;

    const addButton = (label, page, disabled = false, current = false) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `btn btn-ghost btn-sm${current ? " is-current" : ""}`;
      button.textContent = label;
      button.disabled = disabled;
      if (current) button.setAttribute("aria-current", "page");
      button.addEventListener("click", () => loadGames(page));
      pagination.appendChild(button);
    };

    addButton("Anterior", Math.max(1, currentPage - 1), !meta.tem_anterior);
    const start = Math.max(1, currentPage - 2);
    const end = Math.min(pages, start + 4);
    const adjustedStart = Math.max(1, end - 4);
    for (let page = adjustedStart; page <= end; page += 1) {
      addButton(String(page), page, false, page === currentPage);
    }
    addButton("Próxima", Math.min(pages, currentPage + 1), !meta.tem_proxima);
  }

  function openForm(game) {
    editingId = game ? game.id : null;
    formTitle.textContent = game ? `Editar "${game.titulo}"` : "Adicionar jogo";
    form.elements.titulo.value = game?.titulo || "";
    form.elements.status.value = game?.status || "quero_jogar";
    form.elements.prioridade.value = game?.prioridade || "normal";
    form.elements.favorito.checked = Boolean(game?.favorito);
    form.elements.nota.value = game?.nota ?? "";
    form.elements.tempo_jogado_horas.value = game?.tempo_jogado_horas ?? 0;
    form.elements.total_conquistas.value = game?.total_conquistas ?? 0;
    form.elements.conquistas_obtidas.value = game?.conquistas_obtidas ?? 0;
    form.elements.categorias.value = (game?.categorias || []).join(", ");
    if (!formCard.open) formCard.showModal();
    form.elements.titulo.focus();
  }

  function closeForm() {
    form.reset();
    form.elements.prioridade.value = "normal";
    editingId = null;
    if (formCard.open) formCard.close();
  }

  function closeOnBackdrop() {
    formCard.addEventListener("click", (event) => {
      const rect = formCard.getBoundingClientRect();
      const inside = event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom;
      if (!inside) closeForm();
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const titulo = form.elements.titulo.value.trim();
    if (!titulo) {
      SavePointUI.showToast("Informe o título do jogo.", { isError: true });
      return;
    }

    const numero = (campo) => {
      const valor = Number(form.elements[campo].value);
      return Number.isFinite(valor) && valor > 0 ? Math.round(valor) : 0;
    };

    const payload = {
      id: editingId,
      titulo,
      status: form.elements.status.value,
      prioridade: form.elements.prioridade.value,
      favorito: form.elements.favorito.checked,
      nota: form.elements.nota.value ? Number(form.elements.nota.value) : null,
      categorias: form.elements.categorias.value.split(",").map((c) => c.trim()).filter(Boolean),
      tempo_jogado_horas: numero("tempo_jogado_horas"),
      total_conquistas: numero("total_conquistas"),
      conquistas_obtidas: numero("conquistas_obtidas"),
    };

    if (payload.conquistas_obtidas > payload.total_conquistas) {
      SavePointUI.showToast("Conquistas obtidas não podem passar do total.", { isError: true });
      return;
    }

    try {
      const wasEditing = Boolean(editingId);
      await SavePointAPI.saveGame(payload);
      SavePointUI.showToast(wasEditing ? "Jogo atualizado." : "Jogo adicionado ao backlog.");
      closeForm();
      await loadGames(wasEditing ? currentPage : 1);
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível salvar o jogo.", { isError: true });
    }
  }

  async function handleDelete(game) {
    const confirmed = window.confirm(`Excluir "${game.titulo}"? As runs e builds associadas também serão excluídas.`);
    if (!confirmed) return;
    try {
      await SavePointAPI.deleteGame(game.id);
      SavePointUI.showToast("Jogo removido.");
      await loadGames(currentPage);
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível remover o jogo.", { isError: true });
    }
  }

  function filtersChanged() {
    currentPage = 1;
    loadGames(1);
  }

  function clearFilters() {
    searchInput.value = "";
    statusFilter.value = "";
    categoryFilter.value = "";
    priorityFilter.value = "";
    originFilter.value = "";
    sortFilter.value = "titulo_asc";
    favoriteFilter.checked = false;
    achievementsFilter.checked = false;
    filtersChanged();
  }

  async function openRequestedEdit() {
    if (!Number.isInteger(requestedEditId) || requestedEditId <= 0) return;
    try {
      const game = await SavePointAPI.getGame(requestedEditId);
      openForm(game);
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível abrir o jogo para edição.", { isError: true });
    }
  }

  document.getElementById("filters-form").addEventListener("submit", (event) => event.preventDefault());
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(filtersChanged, 300);
  });
  [statusFilter, categoryFilter, priorityFilter, originFilter, sortFilter, favoriteFilter, achievementsFilter]
    .forEach((element) => element.addEventListener("change", filtersChanged));
  clearFiltersButton.addEventListener("click", clearFilters);
  addButton.addEventListener("click", () => openForm(null));
  cancelButton.addEventListener("click", closeForm);
  closeButton.addEventListener("click", closeForm);
  formCard.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeForm();
  });
  closeOnBackdrop();
  form.addEventListener("submit", handleSubmit);
  document.addEventListener("savepoint:steam-synced", () => loadGames(1));

  loadGames(currentPage).then(openRequestedEdit);
})();
