(function () {
  const grid = document.getElementById("runs-grid");
  const emptyState = document.getElementById("empty-state");
  const jogoFilter = document.getElementById("run-jogo-filter");
  const resultadoFilter = document.getElementById("run-resultado-filter");

  let allRuns = [];
  let titulosPorJogoId = {};

  async function loadRuns() {
    try {
      const [runs, games] = await Promise.all([
        SavePointAPI.getRuns(),
        SavePointAPI.getGames(),
      ]);

      allRuns = runs;
      titulosPorJogoId = {};
      games.forEach((game) => {
        titulosPorJogoId[game.id] = game.titulo;
      });

      populateJogoFilter(games);
      renderRuns();
    } catch (err) {
      SavePointUI.showToast("Não foi possível carregar o histórico de runs.", {
        isError: true,
      });
      console.error(err);
    }
  }

  function populateJogoFilter(games) {
    const comRuns = games.filter((game) =>
      allRuns.some((run) => run.jogo_id === game.id),
    );
    const atual = jogoFilter.value;

    jogoFilter.innerHTML =
      '<option value="">Jogo: todos</option>' +
      comRuns
        .map(
          (game) =>
            `<option value="${game.id}">${SavePointUI.escapeHtml(game.titulo)}</option>`,
        )
        .join("");
    jogoFilter.value = atual;
  }

  function getFilteredRuns() {
    const jogoId = jogoFilter.value;
    const resultado = resultadoFilter.value;

    return allRuns.filter((run) => {
      const matchesJogo = !jogoId || String(run.jogo_id) === jogoId;
      const matchesResultado = !resultado || run.resultado === resultado;
      return matchesJogo && matchesResultado;
    });
  }

  function formatarData(iso) {
    const [ano, mes, dia] = iso.split("-");
    return `${dia}/${mes}/${ano}`;
  }

  function renderRuns() {
    const runs = getFilteredRuns();
    grid.innerHTML = "";

    if (runs.length === 0) {
      emptyState.hidden = false;
      return;
    }
    emptyState.hidden = true;

    runs.forEach((run) => grid.appendChild(renderCard(run)));
  }

  function renderCard(run) {
    const titulo = titulosPorJogoId[run.jogo_id] || "Jogo removido";
    const vitoria = run.resultado === "vitoria";

    const article = document.createElement("article");
    article.className = "card";
    article.setAttribute(
      "aria-label",
      `Run de ${titulo} em ${formatarData(run.data)}`,
    );

    article.innerHTML = `
      <div class="game-card__meta">
        <span class="badge ${vitoria ? "badge--zerado" : "badge--abandonado"}">
          ${vitoria ? "Vitória" : "Derrota"}
        </span>
        <span class="hint">${formatarData(run.data)}</span>
      </div>
      <h3 class="game-card__title">${SavePointUI.escapeHtml(titulo)}</h3>
      <p class="hint" style="margin: 0;">Duração</p>
      <p style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; margin: 0 0 var(--space-3);">
        ${run.tempo_duracao}
      </p>
      ${
        run.causa_morte
          ? `<p class="hint" style="margin:0;">Causa da morte</p>
             <p style="margin: 0 0 var(--space-3);">${SavePointUI.escapeHtml(run.causa_morte)}</p>`
          : ""
      }
      <div class="game-card__actions">
        <button type="button" class="btn btn-danger-outline btn-sm" data-action="delete">Excluir run</button>
      </div>
    `;

    article
      .querySelector('[data-action="delete"]')
      .addEventListener("click", () => handleDelete(run, titulo));
    return article;
  }

  async function handleDelete(run, titulo) {
    const confirmado = window.confirm(
      `Excluir a run de "${titulo}" de ${formatarData(run.data)}?`,
    );
    if (!confirmado) return;

    try {
      await SavePointAPI.deleteRun(run.id);
      SavePointUI.showToast("Run excluída.");
      await loadRuns();
    } catch (err) {
      SavePointUI.showToast(err.message || "Não foi possível excluir a run.", {
        isError: true,
      });
    }
  }

  jogoFilter.addEventListener("change", renderRuns);
  resultadoFilter.addEventListener("change", renderRuns);

  loadRuns();
})();
