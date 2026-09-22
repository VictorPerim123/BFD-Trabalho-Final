const SavePointAPI = (() => {
  const ENDPOINTS = {
    games: "/api/jogos",
    runs: "/api/runs",
    builds: "/api/builds",
    estatisticas: "/api/estatisticas",
  };

  function tokenCsrf() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
  }

  async function requisitar(url, options = {}) {
    const metodo = (options.method || "GET").toUpperCase();
    const headers = {};
    if (options.body) headers["Content-Type"] = "application/json";
    if (metodo !== "GET") headers["X-CSRFToken"] = tokenCsrf();

    const res = await fetch(url, {
      credentials: "same-origin",
      ...options,
      headers: { ...headers, ...(options.headers || {}) },
    });

    if (res.status === 401) {
      window.location.href = "/login";
      throw new Error("Sessão expirada.");
    }

    if (!res.ok) {
      let mensagem = `Erro HTTP ${res.status}`;
      try {
        const corpo = await res.json();
        if (corpo && corpo.erro) mensagem = corpo.erro;
      } catch {

      }
      throw new Error(mensagem);
    }

    if (res.status === 204) return null;
    return res.json();
  }

  function getGames() {
    return requisitar(ENDPOINTS.games);
  }

  function saveGame(game) {
    if (game.id) {
      return requisitar(`${ENDPOINTS.games}/${game.id}`, {
        method: "PUT",
        body: JSON.stringify(game),
      });
    }
    return requisitar(ENDPOINTS.games, {
      method: "POST",
      body: JSON.stringify(game),
    });
  }

  function deleteGame(id) {
    return requisitar(`${ENDPOINTS.games}/${id}`, { method: "DELETE" });
  }

  function getRuns() {
    return requisitar(ENDPOINTS.runs);
  }

  function getRun(id) {
    return requisitar(`${ENDPOINTS.runs}/${id}`);
  }

  function saveRun(run) {
    if (run.id) {
      return requisitar(`${ENDPOINTS.runs}/${run.id}`, {
        method: "PUT",
        body: JSON.stringify(run),
      });
    }
    return requisitar(ENDPOINTS.runs, {
      method: "POST",
      body: JSON.stringify(run),
    });
  }

  function deleteRun(id) {
    return requisitar(`${ENDPOINTS.runs}/${id}`, { method: "DELETE" });
  }

  function getBuilds() {
    return requisitar(ENDPOINTS.builds);
  }

  function getBuild(id) {
    return requisitar(`${ENDPOINTS.builds}/${id}`);
  }

  function saveBuild(build) {
    if (build.id) {
      return requisitar(`${ENDPOINTS.builds}/${build.id}`, {
        method: "PUT",
        body: JSON.stringify(build),
      });
    }
    return requisitar(ENDPOINTS.builds, {
      method: "POST",
      body: JSON.stringify(build),
    });
  }

  function deleteBuild(id) {
    return requisitar(`${ENDPOINTS.builds}/${id}`, { method: "DELETE" });
  }

  function getEstatisticas() {
    return requisitar(ENDPOINTS.estatisticas);
  }

  return {
    getGames,
    saveGame,
    deleteGame,
    getRuns,
    getRun,
    saveRun,
    deleteRun,
    getBuilds,
    getBuild,
    saveBuild,
    deleteBuild,
    getEstatisticas,
  };
})();
