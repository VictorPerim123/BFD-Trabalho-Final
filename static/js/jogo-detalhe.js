(function () {
  const root = document.querySelector(".game-detail");
  if (!root) return;

  const gameId = Number(root.dataset.gameId);
  const favoriteButton = document.getElementById("detail-favorite");
  const prioritySelect = document.getElementById("detail-priority");
  const deleteButton = document.getElementById("btn-delete-game");
  const tabs = Array.from(document.querySelectorAll("[data-detail-tab]"));
  const panels = Array.from(document.querySelectorAll("[data-detail-panel]"));

  function ativarAba(nome, atualizarHash) {
    if (!tabs.some((tab) => tab.dataset.detailTab === nome)) nome = "visao-geral";
    tabs.forEach((tab) => {
      const ativa = tab.dataset.detailTab === nome;
      tab.classList.toggle("is-active", ativa);
      tab.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    panels.forEach((panel) => {
      panel.hidden = panel.dataset.detailPanel !== nome;
    });
    if (atualizarHash) history.replaceState(null, "", `#${nome}`);
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => ativarAba(tab.dataset.detailTab, true));
  });

  const hashInicial = window.location.hash.replace(/^#/, "");
  ativarAba(hashInicial || "visao-geral", false);

  if (favoriteButton) {
    favoriteButton.addEventListener("click", async () => {
      const current = favoriteButton.getAttribute("aria-pressed") === "true";
      try {
        const game = await SavePointAPI.updateGamePreferences(gameId, { favorito: !current });
        favoriteButton.classList.toggle("is-active", game.favorito);
        favoriteButton.setAttribute("aria-pressed", game.favorito ? "true" : "false");
        favoriteButton.setAttribute("aria-label", game.favorito ? "Remover dos favoritos" : "Adicionar aos favoritos");
      } catch (err) {
        SavePointUI.showToast(err.message || "Não foi possível alterar o favorito.", { isError: true });
      }
    });
  }

  if (prioritySelect) {
    prioritySelect.dataset.previous = prioritySelect.value;
    prioritySelect.addEventListener("change", async () => {
      const previous = prioritySelect.dataset.previous || "";
      try {
        const game = await SavePointAPI.updateGamePreferences(gameId, { prioridade: prioritySelect.value });
        prioritySelect.value = game.prioridade;
        prioritySelect.dataset.previous = game.prioridade;
        SavePointUI.showToast("Prioridade atualizada.");
      } catch (err) {
        if (previous) prioritySelect.value = previous;
        SavePointUI.showToast(err.message || "Não foi possível alterar a prioridade.", { isError: true });
      }
    });
  }

  if (deleteButton) {
    deleteButton.addEventListener("click", async () => {
      if (!window.confirm("Excluir este jogo? As runs, builds, conquistas, desafios e histórico associados também serão excluídos.")) return;
      try {
        await SavePointAPI.deleteGame(gameId);
        window.location.href = "/backlog";
      } catch (err) {
        SavePointUI.showToast(err.message || "Não foi possível excluir o jogo.", { isError: true });
      }
    });
  }

  const achievementList = document.getElementById("achievement-list");
  const achievementSearch = document.getElementById("achievement-search");
  const achievementFilter = document.getElementById("achievement-filter");
  const achievementSort = document.getElementById("achievement-sort");
  const achievementEmpty = document.getElementById("achievement-filter-empty");

  if (achievementList && achievementSearch && achievementFilter && achievementSort) {
    const items = Array.from(achievementList.querySelectorAll("[data-achievement-item]"));
    const normalizar = (texto) => texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");

    function aplicarFiltrosConquistas() {
      const busca = normalizar(achievementSearch.value.trim());
      const filtro = achievementFilter.value;
      const ordenacao = achievementSort.value;
      const ordenados = [...items].sort((a, b) => {
        const nomeA = a.dataset.name || "";
        const nomeB = b.dataset.name || "";
        if (ordenacao === "nome") return nomeA.localeCompare(nomeB, "pt-BR");
        if (ordenacao === "recentes") {
          const dataA = a.dataset.unlockedAt || "";
          const dataB = b.dataset.unlockedAt || "";
          if (dataA !== dataB) return dataB.localeCompare(dataA);
          return nomeA.localeCompare(nomeB, "pt-BR");
        }
        const unlockedA = a.dataset.unlocked === "1" ? 1 : 0;
        const unlockedB = b.dataset.unlocked === "1" ? 1 : 0;
        if (unlockedA !== unlockedB) return unlockedB - unlockedA;
        return nomeA.localeCompare(nomeB, "pt-BR");
      });

      let visiveis = 0;
      ordenados.forEach((item) => {
        const desbloqueada = item.dataset.unlocked === "1";
        const nome = normalizar(item.dataset.name || "");
        const correspondeBusca = !busca || nome.includes(busca);
        const correspondeFiltro = filtro === "todas"
          || (filtro === "desbloqueadas" && desbloqueada)
          || (filtro === "bloqueadas" && !desbloqueada);
        const visivel = correspondeBusca && correspondeFiltro;
        item.hidden = !visivel;
        if (visivel) visiveis += 1;
        achievementList.appendChild(item);
      });
      if (achievementEmpty) achievementEmpty.hidden = visiveis !== 0;
    }

    achievementSearch.addEventListener("input", aplicarFiltrosConquistas);
    achievementFilter.addEventListener("change", aplicarFiltrosConquistas);
    achievementSort.addEventListener("change", aplicarFiltrosConquistas);
    aplicarFiltrosConquistas();
  }
})();
