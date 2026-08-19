(function () {
  const grid = document.getElementById("builds-grid");
  const emptyState = document.getElementById("empty-state");

  async function loadBuilds() {
    try {
      const [builds, games] = await Promise.all([
        SavePointAPI.getBuilds(),
        SavePointAPI.getGames(),
      ]);
      const gamesById = new Map(games.map((g) => [g.id, g]));
      render(builds, gamesById);
    } catch (err) {
      SavePointUI.showToast("Não foi possível carregar as builds.", { isError: true });
      console.error(err);
    }
  }

  function render(builds, gamesById) {
    grid.innerHTML = "";
    if (builds.length === 0) {
      emptyState.hidden = false;
      return;
    }
    emptyState.hidden = true;

    builds.forEach((build) => {
      const jogo = gamesById.get(build.jogo_id);
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <p class="hint" style="margin-bottom:0.25rem;">${SavePointUI.escapeHtml(jogo?.titulo || "Jogo não encontrado")}</p>
        <h3 style="margin-bottom:0.5rem;">${SavePointUI.escapeHtml(build.nome_build)}</h3>
        <p><strong>Equipamento:</strong> ${SavePointUI.escapeHtml(build.detalhes_equipamento)}</p>
        <p style="margin-bottom:0;"><strong>Habilidades:</strong> ${SavePointUI.escapeHtml(build.habilidades)}</p>
      `;
      grid.appendChild(card);
    });
  }

  loadBuilds();
})();
