(function () {
  const statusLabels = {
    quero_jogar: "Quero jogar",
    jogando: "Jogando",
    jogado: "Jogado",
    zerado: "Zerado",
    platinado: "Platinado",
    abandonado: "Abandonado",
  };

  function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
  }

  function clampPercentage(value) {
    return Math.max(0, Math.min(100, Math.round(value || 0)));
  }

  function emptyState(message, actionLabel, href) {
    const action = actionLabel && href
      ? `<a class="btn btn-ghost btn-sm" href="${href}">${SavePointUI.escapeHtml(actionLabel)}</a>`
      : "";
    return `
      <div class="dashboard-empty">
        <p>${SavePointUI.escapeHtml(message)}</p>
        ${action}
      </div>
    `;
  }

  function renderHero(stats) {
    const totalGames = stats.total_jogos || 0;
    const finishedGames = stats.jogos_zerados || 0;
    const libraryPct = totalGames ? (finishedGames / totalGames) * 100 : 0;
    const totalAchievements = stats.total_conquistas || 0;
    const earnedAchievements = stats.conquistas_obtidas || 0;
    const achievementPct = totalAchievements ? (earnedAchievements / totalAchievements) * 100 : 0;

    setText("library-progress-label", `${clampPercentage(libraryPct)}%`);
    setText("achievement-progress-label", `${clampPercentage(achievementPct)}%`);
    document.getElementById("library-progress-bar").style.width = `${clampPercentage(libraryPct)}%`;
    document.getElementById("achievement-progress-bar").style.width = `${clampPercentage(achievementPct)}%`;

    setText(
      "library-progress-copy",
      totalGames
        ? `${finishedGames} de ${totalGames} jogo(s) marcados como zerados ou platinados.`
        : "Adicione jogos ao backlog para começar a acompanhar sua jornada."
    );
    setText(
      "achievement-progress-copy",
      totalAchievements
        ? `${earnedAchievements} de ${totalAchievements} conquistas desbloqueadas.`
        : "Sincronize jogos da Steam para acompanhar conquistas."
    );
  }

  function renderMetrics(stats) {
    setText("stat-games", stats.total_jogos || 0);
    setText("stat-hours", SavePointUI.formatHoras(stats.horas_totais || 0));
    setText("stat-runs", stats.total_runs || 0);
    setText("stat-rating", stats.nota_media == null ? "—" : Number(stats.nota_media).toFixed(1));
    setText(
      "stat-games-meta",
      `${stats.jogando || 0} jogando · ${stats.favoritos || 0} favorito(s)`
    );
    setText(
      "stat-rating-meta",
      stats.nota_media == null ? "avalie jogos para calcular" : "média das suas avaliações"
    );
  }

  function renderPlaying(stats) {
    const games = stats.jogando_agora || [];
    const root = document.getElementById("playing-now");
    if (!games.length) {
      root.innerHTML = emptyState(
        "Nenhum jogo está marcado como Jogando agora.",
        "Escolher próximo jogo",
        "/backlog?status=quero_jogar"
      );
      return;
    }

    root.innerHTML = `<div class="dashboard-playing-list">${games.map((game) => `
      <a class="dashboard-playing-item" href="/jogos/${game.id}">
        <div class="dashboard-playing-item__main">
          <span class="badge badge--jogando">Jogando</span>
          <strong>${SavePointUI.escapeHtml(game.titulo)}</strong>
        </div>
        <div class="dashboard-playing-item__meta">
          <span>${SavePointUI.formatHoras(game.tempo_jogado_horas)} jogadas</span>
          ${game.percentual_conquistas ? `<span>${game.percentual_conquistas}% conquistas</span>` : ""}
          <span aria-hidden="true">→</span>
        </div>
      </a>
    `).join("")}</div>`;
  }

  function renderHealth(stats) {
    const health = stats.saude || {};
    const entries = [
      ["Nunca iniciados", health.nunca_iniciados || 0],
      ["Jogando", health.jogando || 0],
      ["Jogados", health.jogados || 0],
      ["Finalizados", health.finalizados || 0],
      ["Abandonados", health.abandonados || 0],
      ["Favoritos", health.favoritos || 0],
    ];
    document.getElementById("health-grid").innerHTML = entries
      .map(([label, value]) => `<div class="health-item"><span>${label}</span><strong>${value}</strong></div>`)
      .join("");

    const added = health.adicionados_30_dias || 0;
    const finished = health.concluidos_30_dias || 0;
    const difference = added - finished;
    const balance = document.getElementById("health-balance");
    const signal = difference > 0 ? `+${difference}` : String(difference);
    const title = difference > 0 ? "Backlog cresceu" : difference < 0 ? "Backlog diminuiu" : "Backlog estável";
    balance.innerHTML = `
      <strong>${SavePointUI.escapeHtml(title)} <span>${SavePointUI.escapeHtml(signal)}</span></strong>
      <p>${added} adicionado(s) e ${finished} concluído(s) nos últimos 30 dias.</p>
    `;
  }

  function renderDistribution(stats) {
    const distribution = stats.distribuicao_status || {};
    const total = Math.max(stats.total_jogos || 0, 1);
    document.getElementById("status-distribution").innerHTML = Object.entries(statusLabels)
      .map(([key, label]) => {
        const value = distribution[key] || 0;
        const percentage = Math.round((value / total) * 100);
        return `
          <a class="distribution-row" href="/backlog?status=${key}">
            <div class="progress-label">
              <span>${SavePointUI.escapeHtml(label)}</span>
              <span>${value} · ${percentage}%</span>
            </div>
            <div class="progress-track" aria-label="${SavePointUI.escapeHtml(label)}: ${percentage}% da biblioteca">
              <div class="progress-fill progress-fill--status" data-status="${key}" style="width:${percentage}%"></div>
            </div>
          </a>
        `;
      })
      .join("");
  }

  function renderAlmostComplete(stats) {
    const games = stats.quase_concluidos || [];
    const root = document.getElementById("almost-complete");
    setText("almost-count", String(stats.saude?.quase_concluidos || games.length));
    if (!games.length) {
      root.innerHTML = emptyState(
        "Nenhum jogo está entre 70% e 99% das conquistas.",
        "Explorar backlog",
        "/backlog?com_conquistas=true&ordenar=progresso_desc"
      );
      return;
    }
    root.innerHTML = `<div class="dashboard-progress-list">${games.map((game) => `
      <a class="dashboard-progress-item" href="/jogos/${game.id}">
        <div class="dashboard-progress-item__heading">
          <div>
            <strong>${SavePointUI.escapeHtml(game.titulo)}</strong>
            <span>${game.obtidas}/${game.total} conquistas</span>
          </div>
          <strong>${game.percentual}%</strong>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width:${clampPercentage(game.percentual)}%"></div>
        </div>
      </a>
    `).join("")}</div>`;
  }

  function renderChallenges(stats) {
    const challenges = stats.desafios_ativos || [];
    const root = document.getElementById("active-challenges");
    if (!challenges.length) {
      root.innerHTML = emptyState("Nenhum desafio ativo.", "Criar desafio", "/desafios");
      return;
    }
    root.innerHTML = `<div class="compact-list">${challenges.map((challenge) => `
      <a class="compact-list__item compact-list__link" href="/desafios">
        <div>
          <strong>${SavePointUI.escapeHtml(challenge.titulo)}</strong>
          <span class="hint">${SavePointUI.escapeHtml(challenge.progresso || "Sem progresso registrado")}</span>
        </div>
        <span class="badge badge--jogando">${SavePointUI.escapeHtml(challenge.tipo)}</span>
      </a>
    `).join("")}</div>`;
  }

  function renderActivity(stats) {
    const events = stats.historico_recente || [];
    const root = document.getElementById("recent-activity");
    if (!events.length) {
      root.innerHTML = emptyState(
        "As próximas mudanças importantes na sua jornada aparecerão aqui.",
        "Abrir backlog",
        "/backlog"
      );
      return;
    }
    root.innerHTML = `<div class="dashboard-timeline">${events.map((event) => `
      <a class="dashboard-timeline__item" href="/jogos/${event.jogo_id}">
        <span class="dashboard-timeline__marker" aria-hidden="true"></span>
        <div>
          <strong>${SavePointUI.escapeHtml(event.descricao)}</strong>
          <span>${SavePointUI.escapeHtml(event.titulo_jogo)}</span>
        </div>
      </a>
    `).join("")}</div>`;
  }

  function renderHighlights(stats) {
    const items = [];
    if (stats.pb_recente) {
      items.push(`
        <a class="highlight-item" href="/jogos/${stats.pb_recente.jogo_id}">
          <span class="badge badge--platinado">PB</span>
          <div>
            <strong>${SavePointUI.escapeHtml(stats.pb_recente.titulo_jogo)}</strong>
            <span class="hint">${SavePointUI.escapeHtml(stats.pb_recente.categoria)} · ${stats.pb_recente.tempo}</span>
          </div>
        </a>
      `);
    }
    for (const build of stats.builds_recentes || []) {
      items.push(`
        <a class="highlight-item" href="/jogos/${build.jogo_id}">
          <span class="badge">Build</span>
          <div>
            <strong>${SavePointUI.escapeHtml(build.nome)}</strong>
            <span class="hint">${SavePointUI.escapeHtml(build.titulo_jogo)} · ${SavePointUI.escapeHtml(build.status.replace("_", " "))}</span>
          </div>
        </a>
      `);
    }
    document.getElementById("journey-highlights").innerHTML = items.length
      ? `<div class="highlight-list">${items.slice(0, 4).join("")}</div>`
      : emptyState("Crie uma build ou registre uma run para destacar sua evolução.", "Abrir jornada", "/jornada");
  }

  function setLoadingState(isLoading) {
    const root = document.getElementById("dashboard-root");
    if (root) root.setAttribute("aria-busy", isLoading ? "true" : "false");
    const retry = document.getElementById("dashboard-retry");
    if (retry) retry.disabled = isLoading;
  }

  async function loadDashboard() {
    const errorBox = document.getElementById("dashboard-error");
    errorBox.hidden = true;
    setLoadingState(true);
    try {
      const stats = await SavePointAPI.getEstatisticas();
      renderHero(stats);
      renderMetrics(stats);
      renderPlaying(stats);
      renderHealth(stats);
      renderDistribution(stats);
      renderAlmostComplete(stats);
      renderChallenges(stats);
      renderActivity(stats);
      renderHighlights(stats);
    } catch (err) {
      errorBox.hidden = false;
      SavePointUI.showToast("Não foi possível carregar o dashboard.", { isError: true });
      console.error(err);
    } finally {
      setLoadingState(false);
    }
  }

  document.getElementById("dashboard-retry").addEventListener("click", loadDashboard);
  document.addEventListener("savepoint:steam-synced", loadDashboard);
  loadDashboard();
})();
