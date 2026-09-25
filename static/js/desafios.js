(function () {
  const grid = document.getElementById("challenges-grid");
  const empty = document.getElementById("challenge-empty");
  const formCard = document.getElementById("challenge-form-card");
  const form = document.getElementById("challenge-form");
  const addButton = document.getElementById("btn-add-challenge");
  const cancelButton = document.getElementById("btn-cancel-challenge-form");
  const closeButton = document.getElementById("btn-close-challenge-form");
  const title = document.getElementById("challenge-form-title");
  const gameSelect = document.getElementById("challenge-game");
  const statusFilter = document.getElementById("challenge-status-filter");
  const typeFilter = document.getElementById("challenge-type-filter");

  let challenges = [];
  let games = [];
  let editingId = null;

  function todayISO() {
    const now = new Date();
    const offset = now.getTimezoneOffset();
    return new Date(now.getTime() - offset * 60000).toISOString().slice(0, 10);
  }

  function formatDate(value) {
    if (!value) return "Sem prazo";
    const [year, month, day] = value.split("-");
    return `${day}/${month}/${year}`;
  }

  function gameTitle(id) {
    const game = games.find((item) => item.id === id);
    return game ? game.titulo : null;
  }

  function populateGames() {
    gameSelect.innerHTML = '<option value="">Nenhum jogo específico</option>' + games
      .map((game) => `<option value="${game.id}">${SavePointUI.escapeHtml(game.titulo)}</option>`)
      .join("");
  }

  function openForm(challenge = null) {
    editingId = challenge ? challenge.id : null;
    title.textContent = challenge ? "Editar desafio" : "Novo desafio";
    form.reset();
    document.getElementById("challenge-start").value = challenge?.data_inicio || todayISO();
    if (challenge) {
      document.getElementById("challenge-title").value = challenge.titulo || "";
      gameSelect.value = challenge.jogo_id ? String(challenge.jogo_id) : "";
      document.getElementById("challenge-type").value = challenge.tipo;
      document.getElementById("challenge-status").value = challenge.status;
      document.getElementById("challenge-goal").value = challenge.meta || "";
      document.getElementById("challenge-progress").value = challenge.progresso || "";
      document.getElementById("challenge-deadline").value = challenge.data_limite || "";
      document.getElementById("challenge-description").value = challenge.descricao || "";
    }
    if (!formCard.open) formCard.showModal();
    document.getElementById("challenge-title").focus();
  }

  function closeForm() {
    editingId = null;
    form.reset();
    if (formCard.open) formCard.close();
  }

  function closeOnBackdrop() {
  formCard.addEventListener("click", (event) => {
        if (event.target === formCard) {
      const rect = formCard.getBoundingClientRect();
      const inside =
        event.clientX >= rect.left &&
        event.clientX <= rect.right &&
        event.clientY >= rect.top &&
        event.clientY <= rect.bottom;
      if (!inside) closeForm();
    }
  });
}

  function filteredChallenges() {
    return challenges.filter((challenge) => {
      const statusMatches = !statusFilter.value || challenge.status === statusFilter.value;
      const typeMatches = !typeFilter.value || challenge.tipo === typeFilter.value;
      return statusMatches && typeMatches;
    });
  }

  function render() {
    const items = filteredChallenges();
    grid.innerHTML = "";
    empty.hidden = items.length > 0;
    items.forEach((challenge) => {
      const card = document.createElement("article");
      card.className = "card";
      const linkedGame = gameTitle(challenge.jogo_id);
      const statusLabel = {
        ativo: "Ativo",
        concluido: "Concluído",
        cancelado: "Cancelado",
      }[challenge.status] || challenge.status;
      const typeLabel = {
        backlog: "Backlog",
        conquistas: "Conquistas",
        speedrun: "Speedrun",
        personalizado: "Personalizado",
      }[challenge.tipo] || challenge.tipo;
      card.innerHTML = `
        <div class="game-card__meta">
          <span class="badge ${challenge.status === "concluido" ? "badge--zerado" : challenge.status === "cancelado" ? "badge--abandonado" : "badge--jogando"}">${statusLabel}</span>
          <span class="hint">${typeLabel}</span>
        </div>
        <h3 class="game-card__title">${SavePointUI.escapeHtml(challenge.titulo)}</h3>
        ${linkedGame ? `<p class="hint" style="margin:0;"><a href="/jogos/${challenge.jogo_id}">${SavePointUI.escapeHtml(linkedGame)}</a></p>` : ""}
        ${challenge.descricao ? `<p>${SavePointUI.escapeHtml(challenge.descricao)}</p>` : ""}
        <div class="challenge-progress-row">
          <div><span class="hint">Meta</span><strong>${SavePointUI.escapeHtml(challenge.meta || "—")}</strong></div>
          <div><span class="hint">Progresso</span><strong>${SavePointUI.escapeHtml(challenge.progresso || "—")}</strong></div>
        </div>
        <p class="hint" style="margin:0;">Prazo: ${formatDate(challenge.data_limite)}</p>
        <div class="game-card__actions">
          <button type="button" class="btn btn-ghost btn-sm" data-action="edit">Editar</button>
          ${challenge.status === "ativo" ? '<button type="button" class="btn btn-primary btn-sm" data-action="finish">Concluir</button>' : ""}
          <button type="button" class="btn btn-danger-outline btn-sm" data-action="delete">Excluir</button>
        </div>
      `;
      card.querySelector('[data-action="edit"]').addEventListener("click", () => openForm(challenge));
      const finish = card.querySelector('[data-action="finish"]');
      if (finish) finish.addEventListener("click", () => finishChallenge(challenge));
      card.querySelector('[data-action="delete"]').addEventListener("click", () => deleteChallenge(challenge));
      grid.appendChild(card);
    });
  }

  async function load() {
    try {
      [challenges, games] = await Promise.all([
        SavePointAPI.getChallenges(),
        SavePointAPI.getGames(),
      ]);
      populateGames();
      render();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível carregar os desafios.", { isError: true });
    }
  }

  async function finishChallenge(challenge) {
    try {
      await SavePointAPI.saveChallenge({ ...challenge, status: "concluido" });
      SavePointUI.showToast("Desafio concluído.");
      await load();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível concluir o desafio.", { isError: true });
    }
  }

  async function deleteChallenge(challenge) {
    if (!window.confirm(`Excluir o desafio "${challenge.titulo}"?`)) return;
    try {
      await SavePointAPI.deleteChallenge(challenge.id);
      SavePointUI.showToast("Desafio excluído.");
      await load();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível excluir o desafio.", { isError: true });
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      id: editingId,
      titulo: document.getElementById("challenge-title").value.trim(),
      jogo_id: gameSelect.value ? Number(gameSelect.value) : null,
      tipo: document.getElementById("challenge-type").value,
      status: document.getElementById("challenge-status").value,
      meta: document.getElementById("challenge-goal").value.trim() || null,
      progresso: document.getElementById("challenge-progress").value.trim() || null,
      data_inicio: document.getElementById("challenge-start").value || todayISO(),
      data_limite: document.getElementById("challenge-deadline").value || null,
      descricao: document.getElementById("challenge-description").value.trim() || null,
    };
    try {
      await SavePointAPI.saveChallenge(payload);
      SavePointUI.showToast(editingId ? "Desafio atualizado." : "Desafio criado.");
      closeForm();
      await load();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível salvar o desafio.", { isError: true });
    }
  });

  document.getElementById("challenge-filters").addEventListener("submit", (event) => event.preventDefault());
  statusFilter.addEventListener("change", render);
  typeFilter.addEventListener("change", render);
  addButton.addEventListener("click", () => openForm());
  cancelButton.addEventListener("click", closeForm);
  closeButton.addEventListener("click", closeForm);
  formCard.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeForm();
  });
  closeOnBackdrop();
  load();
})();
