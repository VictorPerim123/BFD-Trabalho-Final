const SavePointUI = (() => {
  const STATUS_LABELS = {
    quero_jogar: "Quero Jogar",
    jogando: "Jogando",
    zerado: "Zerado",
    platinado: "Platinado",
    abandonado: "Abandonado",
  };

  const STATUS_BADGE_CLASS = {
    quero_jogar: "badge--quero-jogar",
    jogando: "badge--jogando",
    zerado: "badge--zerado",
    platinado: "badge--platinado",
    abandonado: "badge--abandonado",
  };

  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
  }

  function statusLabel(status) {
    return STATUS_LABELS[status] || status;
  }

  function statusBadgeClass(status) {
    return STATUS_BADGE_CLASS[status] || "";
  }

  function showToast(message, { isError = false } = {}) {
    const region = document.getElementById("toast-region");
    if (!region) return;

    region.innerHTML = "";
    const toast = document.createElement("div");
    toast.className = "toast" + (isError ? " toast--error" : "");
    toast.textContent = message;
    region.appendChild(toast);

    window.setTimeout(() => toast.remove(), 3500);
  }

  function formatHoras(horas) {
    if (!horas) return "0h";
    return `${horas}h`;
  }

  return { escapeHtml, statusLabel, statusBadgeClass, showToast, formatHoras, STATUS_LABELS };
})();
