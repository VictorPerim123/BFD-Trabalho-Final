const SavePointAPI = (() => {
  const ENDPOINTS = {
    games: "/api/jogos",
  };

  async function requisitar(url, options = {}) {
    const res = await fetch(url, {
      credentials: "same-origin",
      headers: options.body
        ? { "Content-Type": "application/json" }
        : undefined,
      ...options,
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
      } catch {}
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

  return { getGames, saveGame, deleteGame };
})();
