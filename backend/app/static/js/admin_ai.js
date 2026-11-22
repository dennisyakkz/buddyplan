// AI buddy settings (REQ-BE-081, REQ-BE-082, REQ-BE-092, REQ-BE-093): one form, one save button.
document.addEventListener("DOMContentLoaded", async () => {
    const form = document.getElementById("ai-config-form");
    const keyInput = document.getElementById("ai-api-key");
    const keyHint = document.getElementById("ai-api-key-hint");
    const modelSelect = document.getElementById("ai-model");
    const promptInput = document.getElementById("ai-system-prompt");
    const promptState = document.getElementById("ai-prompt-state");
    const enabledInput = document.getElementById("ai-enabled");
    const settingsFields = document.getElementById("ai-settings-fields");
    const contextInput = document.getElementById("ai-context-messages");
    const debugEnabledInput = document.getElementById("ai-debug-enabled");
    const debugFields = document.getElementById("ai-debug-fields");
    const retentionInput = document.getElementById("ai-debug-retention");
    let config = null;
    let clearKey = false;

    function updateSettingsVisibility() {
        settingsFields.style.display = enabledInput.checked ? "" : "none";
    }

    function updateDebugVisibility() {
        debugFields.style.display = debugEnabledInput.checked ? "" : "none";
    }

    function showConfig(cfg) {
        config = cfg;
        clearKey = false;
        keyInput.value = "";
        keyHint.textContent = cfg.has_api_key ? `(ingesteld: ${cfg.api_key_hint})` : "(niet ingesteld)";
        promptInput.value = cfg.system_prompt;
        enabledInput.checked = cfg.enabled;
        contextInput.value = cfg.context_messages;
        debugEnabledInput.checked = cfg.debug_log_enabled;
        retentionInput.value = cfg.debug_retention_days;
        updatePromptState();
        updateSettingsVisibility();
        updateDebugVisibility();
        setModels(cfg.model ? [{ name: cfg.model, display_name: cfg.model }] : [], cfg.model);
    }

    function updatePromptState() {
        const isDefault = config && promptInput.value.trim() === config.default_system_prompt.trim();
        promptState.textContent = isDefault ? "(standaard)" : "(aangepast)";
    }

    function setModels(models, selected) {
        modelSelect.innerHTML = '<option value="">Kies een model…</option>' + models
            .map(m => `<option value="${escapeHtml(m.name)}">${escapeHtml(m.display_name)} (${escapeHtml(m.name)})</option>`)
            .join("");
        if (selected && !models.some(m => m.name === selected)) {
            modelSelect.insertAdjacentHTML("beforeend", `<option value="${escapeHtml(selected)}">${escapeHtml(selected)}</option>`);
        }
        modelSelect.value = selected || "";
    }

    async function loadModels(quiet) {
        try {
            const models = await api("/api/admin/ai/models", {
                method: "POST",
                body: JSON.stringify({ api_key: keyInput.value.trim() || null }),
            });
            setModels(models, modelSelect.value || config?.model);
            if (!quiet) showToast(`${models.length} modellen gevonden`, "success", 3000);
        } catch (err) {
            if (!quiet) showToast(escapeHtml(err.message), "error");
        }
    }

    document.getElementById("btn-load-models").addEventListener("click", () => loadModels(false));
    document.getElementById("btn-reset-prompt").addEventListener("click", () => {
        promptInput.value = config.default_system_prompt;
        updatePromptState();
    });
    document.getElementById("btn-clear-key").addEventListener("click", () => {
        clearKey = true;
        keyInput.value = "";
        keyHint.textContent = "(wordt verwijderd bij opslaan)";
    });
    promptInput.addEventListener("input", updatePromptState);
    enabledInput.addEventListener("change", updateSettingsVisibility);
    debugEnabledInput.addEventListener("change", updateDebugVisibility);

    try {
        showConfig(await api("/api/admin/ai/config"));
        if (config.has_api_key) loadModels(true);
    } catch (err) {
        showToast("Laden mislukt: " + escapeHtml(err.message), "error");
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const saved = await api("/api/admin/ai/config", {
                method: "PUT",
                body: JSON.stringify({
                    api_key: keyInput.value.trim() || null,
                    clear_api_key: clearKey,
                    model: modelSelect.value,
                    system_prompt: promptInput.value,
                    enabled: enabledInput.checked,
                    context_messages: parseInt(contextInput.value, 10),
                    debug_log_enabled: debugEnabledInput.checked,
                    debug_retention_days: parseInt(retentionInput.value, 10),
                }),
            });
            const selected = modelSelect.value;
            showConfig(saved);
            if (saved.has_api_key) await loadModels(true);
            modelSelect.value = selected && saved.model ? saved.model : "";
            const state = saved.configured
                ? "de AI buddy staat aan"
                : saved.enabled ? "de AI buddy heeft nog een key en een model nodig" : "de AI buddy staat uit";
            showToast(`Instellingen opgeslagen, ${state}`, "success", 4000);
        } catch (err) {
            showToast("Opslaan mislukt: " + escapeHtml(err.message), "error");
        }
    });

    document.getElementById("btn-clear-debug").addEventListener("click", async () => {
        if (!confirm("Alle bewaarde verzoeken en antwoorden wissen? Tokens en kosten blijven bewaard.")) return;
        try {
            const result = await api("/api/admin/ai/calls/content", { method: "DELETE" });
            showToast(`Debug-inhoud van ${result.cleared} aanroepen gewist`, "success", 3000);
        } catch (err) {
            showToast("Wissen mislukt: " + escapeHtml(err.message), "error");
        }
    });
});
