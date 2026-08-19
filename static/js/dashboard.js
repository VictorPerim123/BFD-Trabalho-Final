(function () {
  const elZerados = document.getElementById("stat-zerados");
  const elHoras = document.getElementById("stat-horas");
  const elNota = document.getElementById("stat-nota");
  const elRuns = document.getElementById("stat-runs");
  const recentList = document.getElementById("recent-games-list");

  async function loadDashboard() {
    try {
      const [games, runs] = await Promise.all([
        SavePointAPI.getGames(),
        SavePointAPI.getRuns(),
      ]);
      renderStats(games, runs);
      renderRecent(games);
    } catch (err) {
      SavePointUI.showToast("Não foi possível carregar o dashboard.", { isError: true });
      console.error(err);
    }
  }

  function renderStats(games, runs) {
    const zerados = games.filter((g) => ["zerado", "platinado"].includes(g.status)).length;
    const horasTotais = games.reduce((sum, g) => sum + (g.tempo_jogado_horas || 0), 0);
    const notas = games.map((g) => g.nota).filter((n) => typeof n === "number");
    const mediaNota = notas.length ? (notas.reduce((a, b) => a + b, 0) / notas.length).toFixed(1) : "—";

    elZerados.textContent = zerados;
    elHoras.textContent = SavePointUI.formatHoras(horasTotais);
    elNota.textContent = mediaNota;
    elRuns.textContent = runs.length;
  }

  function renderRecent(games) {
    const recentes = [...games]
      .filter((g) => g.status === "jogando")
      .slice(0, 4);

    recentList.innerHTML = "";
    if (recentes.length === 0) {
      recentList.innerHTML = '<li class="empty-state">Nenhum jogo em andamento.</li>';
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
