const SavePointAPI = (() => {
  const ENDPOINTS = {
    games: "/static/data/games.json",
    runs: "/static/data/runs.json",
    builds: "/static/data/builds.json",
  };

  const LS_KEYS = {
    gamesOverrides: "savepoint_mock_games_overrides",
    runsOverrides: "savepoint_mock_runs_extra",
  };

  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Falha ao buscar ${url}: HTTP ${res.status}`);
    }
    return res.json();
  }

  function readOverrides(key) {
    try {
      return JSON.parse(localStorage.getItem(key) || "{}");
    } catch {
      return {};
    }
  }

  function writeOverrides(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  /* ---------------------- Jogos / Backlog ---------------------- */

  async function getGames() {
    const base = await fetchJSON(ENDPOINTS.games);
    const overrides = readOverrides(LS_KEYS.gamesOverrides);

    const merged = base
      .filter((g) => overrides[g.id]?._deleted !== true)
      .map((g) => ({ ...g, ...(overrides[g.id] || {}) }));

    Object.entries(overrides)
      .filter(([id]) => Number(id) < 0)
      .forEach(([, value]) => merged.push(value));

    return merged;
  }

  async function saveGame(game) {
    const overrides = readOverrides(LS_KEYS.gamesOverrides);
    const id = game.id ?? -Date.now();
    overrides[id] = { ...game, id };
    writeOverrides(LS_KEYS.gamesOverrides, overrides);
    return overrides[id];
  }

  async function deleteGame(id) {
    const overrides = readOverrides(LS_KEYS.gamesOverrides);
    overrides[id] = { ...(overrides[id] || {}), _deleted: true };
    writeOverrides(LS_KEYS.gamesOverrides, overrides);
  }

  /* ---------------------- Runs (roguelike) ---------------------- */

  async function getRuns() {
    const base = await fetchJSON(ENDPOINTS.runs);
    const extra = readOverrides(LS_KEYS.runsOverrides);
    return [...Object.values(extra), ...base];
  }

  async function saveRun(run) {
    const extra = readOverrides(LS_KEYS.runsOverrides);
    const id = -Date.now();
    extra[id] = { ...run, id };
    writeOverrides(LS_KEYS.runsOverrides, extra);
    return extra[id];
  }

  /* ---------------------- Builds ---------------------- */

  async function getBuilds() {
    return fetchJSON(ENDPOINTS.builds);
  }

  return { getGames, saveGame, deleteGame, getRuns, saveRun, getBuilds };
})();
