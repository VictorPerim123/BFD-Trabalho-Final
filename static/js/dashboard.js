(function () {
  const elZerados = document.getElementById("stat-zerados");
  const elHoras = document.getElementById("stat-horas");
  const elNota = document.getElementById("stat-nota");
  const elRuns = document.getElementById("stat-runs");
  const recentList = document.getElementById("recent-games-list");

  async function loadDashboard() {
    try {
      const [stats, games] = await Promise.all([
        SavePointAPI.getEstatisticas(),
        SavePointAPI.getGames(),
      ]);
      renderStats(stats);
      renderRecent(games);
    } catch (err) {
      SavePointUI.showToast("Não foi possível carregar o dashboard.", {
        isError: true,
      });
      console.error(err);
    }
  }

  function renderStats(stats) {
    elZerados.textContent = stats.jogos_zerados;
    elHoras.textContent = SavePointUI.formatHoras(stats.horas_totais);
    elNota.textContent = stats.nota_media != null ? stats.nota_media : "—";
    elRuns.textContent = stats.total_runs;
  }

  function renderRecent(games) {
    const recentes = games.filter((g) => g.status === "jogando").slice(0, 4);

    recentList.innerHTML = "";
    if (recentes.length === 0) {
      recentList.innerHTML =
        '<li class="empty-state">Nenhum jogo em andamento.</li>';
      return;
    }

    recentes.forEach((game) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <span>${SavePointUI.escapeHtml(game.titulo)}</span>
        <span class="badge ${SavePointUI.statusBadgeClass(game.status)}">${SavePointUI.statusLabel(game.status)}</span>
      `;
      recentList.appendChild(li);
    });
  }

  loadDashboard();
})();
