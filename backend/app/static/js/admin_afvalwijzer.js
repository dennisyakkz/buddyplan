let afvalConfig = null;
let afvalPersons = [];

document.addEventListener("DOMContentLoaded", async () => {
    try {
        [afvalConfig, afvalPersons] = await Promise.all([
            api("/api/admin/afvalwijzer"),
            api("/api/admin/users"),
        ]);
        renderAfval();
    } catch (err) {
        showToast(`Laden mislukt: ${err.message}`, "error");
    }

    document.getElementById("afval-enabled").addEventListener("change", onToggleEnabled);
    document.getElementById("btn-sync").addEventListener("click", onSync);
    document.getElementById("btn-create-tasks").addEventListener("click", onCreateTasks);
});

async function onToggleEnabled(e) {
    const checked = e.target.checked;
    try {
        afvalConfig = await api("/api/admin/afvalwijzer", {
            method: "PUT",
            body: JSON.stringify({
                enabled: checked,
                postcode: afvalConfig.postcode,
                huisnummer: afvalConfig.huisnummer,
            }),
        });
        updateAfvalVisibility();
    } catch (err) {
        showToast(`Fout: ${err.message}`, "error");
        e.target.checked = !checked;
    }
}

async function onSync() {
    const postcode = document.getElementById("afval-postcode").value.trim();
    const huisnummer = document.getElementById("afval-huisnummer").value.trim();

    if (!postcode || !huisnummer) {
        showToast("Vul postcode en huisnummer in", "error");
        return;
    }

    const syncStatus = document.getElementById("sync-status");
    const syncBtn = document.getElementById("btn-sync");

    syncBtn.disabled = true;
    syncStatus.textContent = "Bezig met synchroniseren…";

    try {
        await api("/api/admin/afvalwijzer", {
            method: "PUT",
            body: JSON.stringify({ enabled: afvalConfig.enabled, postcode, huisnummer }),
        });
        afvalConfig = await api("/api/admin/afvalwijzer/sync", { method: "POST" });

        syncStatus.textContent = `${afvalConfig.types.length} type(s) gevonden`;
        renderAfvalTypes();
        document.getElementById("afval-types-section").style.display = "";
        showToast("Afvaltypes gesynchroniseerd");
    } catch (err) {
        syncStatus.textContent = "";
        showToast(`Synchronisatie mislukt: ${err.message}`, "error");
    } finally {
        syncBtn.disabled = false;
    }
}

async function onCreateTasks() {
    const btn = document.getElementById("btn-create-tasks");
    btn.disabled = true;
    try {
        const result = await api("/api/admin/afvalwijzer/create-tasks", { method: "POST" });
        showToast(`${result.created} taken aangemaakt voor huidige en komende week`);
    } catch (err) {
        showToast(`Fout: ${err.message}`, "error");
    } finally {
        btn.disabled = false;
    }
}

function renderAfval() {
    document.getElementById("afval-enabled").checked = afvalConfig.enabled;
    document.getElementById("afval-postcode").value = afvalConfig.postcode || "";
    document.getElementById("afval-huisnummer").value = afvalConfig.huisnummer || "";
    updateAfvalVisibility();

    if (afvalConfig.types && afvalConfig.types.length > 0) {
        renderAfvalTypes();
        document.getElementById("afval-types-section").style.display = "";
    }
}

function updateAfvalVisibility() {
    const enabled = afvalConfig.enabled;
    document.getElementById("afval-address-section").style.display = enabled ? "" : "none";
    document.getElementById("btn-create-tasks").classList.toggle("hidden", !enabled);
}

function renderAfvalTypes() {
    const list = document.getElementById("afval-types-list");
    list.innerHTML = (afvalConfig.types || []).map(t => typeItemHtml(t)).join("");

    (afvalConfig.types || []).forEach(async (t) => {
        setupTypeToggle(t.id);
        setupTypeSave(t.id);
        if (t.enabled) {
            initIconPicker(document.getElementById(`picker-buiten-${t.id}`));
            initIconPicker(document.getElementById(`picker-binnen-${t.id}`));
        }
    });
}

function typeItemHtml(t) {
    return `
        <li class="afval-type-item" id="type-item-${t.id}">
            <div class="toggle">
                <span style="font-weight:600;font-size:15px">${escapeHtml(t.type_label || t.waste_type)}</span>
                <label class="switch">
                    <input type="checkbox" id="type-enabled-${t.id}" ${t.enabled ? "checked" : ""}>
                    <span class="slider"></span>
                </label>
            </div>
            <div id="type-details-${t.id}" class="afval-type-details" style="${t.enabled ? "" : "display:none"}">
                ${typeDetailsHtml(t)}
            </div>
        </li>
    `;
}

function typeDetailsHtml(t) {
    return `
        <div class="form-group">
            <label>Naam</label>
            <input type="text" id="type-naam-${t.id}" value="${escapeHtml(t.naam || t.type_label || "")}" placeholder="Naam van dit afvaltype">
        </div>
        <div class="form-group">
            <label>Buiten zetten</label>
            <div class="afval-row">
                <select id="type-buiten-dag-${t.id}">
                    <option value="day_before" ${t.buiten_dag === "day_before" ? "selected" : ""}>1 dag eerder</option>
                    <option value="same_day" ${t.buiten_dag === "same_day" ? "selected" : ""}>Zelfde dag</option>
                </select>
                <select id="type-buiten-person-${t.id}">
                    ${personOptions(t.buiten_person_id)}
                </select>
            </div>
            <div id="picker-buiten-${t.id}" style="margin-top:8px">
                ${createIconPicker(t.buiten_icon || "fas:trash", "buiten_icon")}
            </div>
        </div>
        <div class="form-group">
            <label>Binnen zetten</label>
            <div class="afval-row">
                <select id="type-binnen-dag-${t.id}">
                    <option value="same_day" ${t.binnen_dag === "same_day" ? "selected" : ""}>Zelfde dag</option>
                    <option value="day_after" ${t.binnen_dag === "day_after" ? "selected" : ""}>1 dag later</option>
                </select>
                <select id="type-binnen-person-${t.id}">
                    ${personOptions(t.binnen_person_id)}
                </select>
            </div>
            <div id="picker-binnen-${t.id}" style="margin-top:8px">
                ${createIconPicker(t.binnen_icon || "fas:trash", "binnen_icon")}
            </div>
        </div>
        <div style="margin-top:14px">
            <button type="button" class="btn btn-primary btn-small" id="type-save-${t.id}">Opslaan</button>
        </div>
    `;
}

function personOptions(selectedId) {
    const none = `<option value="">— Niemand —</option>`;
    const opts = afvalPersons.map(p =>
        `<option value="${p.id}" ${p.id === selectedId ? "selected" : ""}>${escapeHtml(p.name)}</option>`
    ).join("");
    return none + opts;
}

// ── Type toggle & save ────────────────────────────────────────────────────────

function setupTypeToggle(typeId) {
    const toggle = document.getElementById(`type-enabled-${typeId}`);
    const details = document.getElementById(`type-details-${typeId}`);

    toggle.addEventListener("change", async (e) => {
        const checked = e.target.checked;
        details.style.display = checked ? "" : "none";

        // Populate details HTML if enabling for the first time
        if (checked && !details.querySelector(`#type-naam-${typeId}`)) {
            const t = afvalConfig.types.find(t => t.id === typeId);
            details.innerHTML = typeDetailsHtml(t);
            initIconPicker(document.getElementById(`picker-buiten-${typeId}`));
            initIconPicker(document.getElementById(`picker-binnen-${typeId}`));
            setupTypeSave(typeId);
        }

        try {
            const updated = await api(`/api/admin/afvalwijzer/types/${typeId}`, {
                method: "PATCH",
                body: JSON.stringify({ enabled: checked }),
            });
            const idx = afvalConfig.types.findIndex(t => t.id === typeId);
            if (idx >= 0) afvalConfig.types[idx] = updated;
        } catch (err) {
            showToast(`Fout: ${err.message}`, "error");
            toggle.checked = !checked;
            details.style.display = toggle.checked ? "" : "none";
        }
    });
}

function setupTypeSave(typeId) {
    const btn = document.getElementById(`type-save-${typeId}`);
    if (!btn) return;
    btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
            await saveType(typeId);
            showToast("Opgeslagen");
        } catch (err) {
            showToast(`Fout: ${err.message}`, "error");
        } finally {
            btn.disabled = false;
        }
    });
}

async function saveType(typeId) {
    const payload = {
        enabled: document.getElementById(`type-enabled-${typeId}`)?.checked ?? false,
        naam: document.getElementById(`type-naam-${typeId}`)?.value.trim() ?? "",
        buiten_dag: document.getElementById(`type-buiten-dag-${typeId}`)?.value ?? "day_before",
        buiten_person_id: parseInt(document.getElementById(`type-buiten-person-${typeId}`)?.value) || null,
        buiten_icon: document.getElementById(`picker-buiten-${typeId}`)?.querySelector("#icon-input")?.value || "fas:trash",
        binnen_dag: document.getElementById(`type-binnen-dag-${typeId}`)?.value ?? "same_day",
        binnen_person_id: parseInt(document.getElementById(`type-binnen-person-${typeId}`)?.value) || null,
        binnen_icon: document.getElementById(`picker-binnen-${typeId}`)?.querySelector("#icon-input")?.value || "fas:trash",
    };

    const updated = await api(`/api/admin/afvalwijzer/types/${typeId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
    });

    const idx = afvalConfig.types.findIndex(t => t.id === typeId);
    if (idx >= 0) afvalConfig.types[idx] = updated;
}
