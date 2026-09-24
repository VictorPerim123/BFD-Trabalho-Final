(function () {
  const initializedRoots = new WeakSet();

  function setLoading(form, loading) {
    const button = form.querySelector("[data-submit-label]");
    const progress = form.querySelector("[data-import-progress]");
    if (button) {
      if (!button.dataset.defaultLabel) button.dataset.defaultLabel = button.textContent;
      button.disabled = loading;
      button.textContent = loading ? form.dataset.loadingLabel || "Processando…" : button.dataset.defaultLabel;
    }
    if (progress) progress.classList.toggle("is-active", loading);
  }

  function updateReclassification(root) {
    const previewForm = root.querySelector("#steam-preview-form");
    if (!previewForm) return;
    const reclassificar = previewForm.querySelector('[name="reclassificar_existentes"]');
    if (!reclassificar) return;
    const automatico = previewForm.querySelector('input[name="classificacao_status"]:checked')?.value === "automatico";
    reclassificar.disabled = !automatico;
    if (!automatico) reclassificar.checked = false;
  }

  async function submitAjax(form) {
    const modalContent = document.getElementById("steam-modal-content");
    setLoading(form, true);
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!response.ok) throw new Error(`Erro HTTP ${response.status}`);
      modalContent.innerHTML = await response.text();
      init(modalContent);
      const resultRoot = modalContent.querySelector("[data-steam-import-root]");
      if (resultRoot?.dataset.steamSynced === "1") {
        document.dispatchEvent(new CustomEvent("savepoint:steam-synced"));
      }
    } catch (error) {
      modalContent.innerHTML = `
        <div class="empty-state" role="alert">
          <strong>Não foi possível processar a integração Steam.</strong>
          <p>Tente novamente ou abra a página completa de importação.</p>
          <a class="btn btn-ghost btn-sm" href="/steam/importar">Abrir importação</a>
        </div>`;
      console.error(error);
    } finally {
      setLoading(form, false);
    }
  }

  function init(root = document) {
    root.querySelectorAll("[data-steam-import-root]").forEach((importRoot) => {
      if (initializedRoots.has(importRoot)) return;
      initializedRoots.add(importRoot);

      const previewForm = importRoot.querySelector("#steam-preview-form");
      if (previewForm) {
        previewForm.querySelectorAll('input[name="classificacao_status"]').forEach((radio) => {
          radio.addEventListener("change", () => updateReclassification(importRoot));
        });
        updateReclassification(importRoot);
      }

      importRoot.querySelectorAll("[data-steam-form]").forEach((form) => {
        form.addEventListener("submit", (event) => {
          if (form.dataset.steamAjax === "1") {
            event.preventDefault();
            submitAjax(form);
            return;
          }
          setLoading(form, true);
        });
      });

      importRoot.querySelectorAll("[data-steam-restart]").forEach((button) => {
        button.addEventListener("click", loadModal);
      });

      importRoot.querySelectorAll("[data-steam-close]").forEach((button) => {
        button.addEventListener("click", closeModal);
      });
    });
  }

  async function loadModal() {
    const dialog = document.getElementById("steam-import-modal");
    const content = document.getElementById("steam-modal-content");
    if (!dialog || !content) return;
    content.innerHTML = '<div class="steam-modal-loading" role="status">Carregando importação Steam…</div>';
    if (!dialog.open) dialog.showModal();
    try {
      const response = await fetch(content.dataset.steamUrl, {
        credentials: "same-origin",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!response.ok) throw new Error(`Erro HTTP ${response.status}`);
      content.innerHTML = await response.text();
      init(content);
      content.querySelector("input[name=identificador]")?.focus();
    } catch (error) {
      content.innerHTML = `
        <div class="empty-state" role="alert">
          <strong>Não foi possível abrir a importação Steam.</strong>
          <p>Tente novamente ou use a página completa.</p>
          <a class="btn btn-ghost btn-sm" href="/steam/importar">Abrir importação</a>
        </div>`;
      console.error(error);
    }
  }

  function closeModal() {
    const dialog = document.getElementById("steam-import-modal");
    if (dialog?.open) dialog.close();
  }

  function setupModal() {
    const dialog = document.getElementById("steam-import-modal");
    if (!dialog) return;
    document.querySelectorAll("[data-steam-modal-trigger]").forEach((trigger) => {
      trigger.addEventListener("click", (event) => {
        event.preventDefault();
        loadModal();
      });
    });
    document.getElementById("btn-close-steam-modal")?.addEventListener("click", closeModal);
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      closeModal();
    });
    dialog.addEventListener("click", (event) => {
      const rect = dialog.getBoundingClientRect();
      const inside = event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom;
      if (!inside) closeModal();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    init(document);
    setupModal();
  });

  window.SavePointSteamImport = { init, open: loadModal };
})();
