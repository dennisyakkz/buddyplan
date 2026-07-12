let me = null;

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatChecked(iso) {
    if (!iso) return "Nog niet getest";
    return new Date(iso).toLocaleString("nl-NL");
}

function formatInterval(minutes) {
    if (minutes === 15) return "Elke 15 minuten";
    if (minutes === 1440) return "Dagelijks";
    return "Elk uur";
}

const FEED_COLORS = [
    { hex: "#e74c3c", name: "Rood" },
    { hex: "#e67e22", name: "Oranje" },
    { hex: "#f1c40f", name: "Geel" },
    { hex: "#27ae60", name: "Groen" },
    { hex: "#1abc9c", name: "Turquoise" },
    { hex: "#3498db", name: "Blauw" },
    { hex: "#2980b9", name: "Donkerblauw" },
    { hex: "#9b59b6", name: "Paars" },
    { hex: "#e91e63", name: "Roze" },
    { hex: "#795548", name: "Bruin" },
    { hex: "#607d8b", name: "Grijs" },
    { hex: "#2c3e50", name: "Antraciet" },
];

function buildColorSwatches(selectedColor) {
    const noneSelected = !selectedColor;
    const swatches = FEED_COLORS.map(c =>
        `<button type="button" class="color-swatch${selectedColor === c.hex ? " selected" : ""}" data-color="${c.hex}" title="${c.name}" style="background:${c.hex}"></button>`
    ).join("");
    return `<button type="button" class="color-swatch swatch-none${noneSelected ? " selected" : ""}" data-color="" title="Geen kleur">✕</button>${swatches}`;
}

function showFeedEditModal(feed, onSave) {
    const interval = feed.sync_interval_minutes || 60;
    const showTimes = feed.show_times || false;
    const hideTitle = feed.hide_title || false;
    showModal(`
        <h2>Externe agenda bewerken</h2>
        <form id="feed-edit-form">
            <div class="form-group">
                <label>Label</label>
                <input type="text" id="feed-edit-label" value="${escapeHtml(feed.label || "")}" placeholder="Optioneel label">
            </div>
            <div class="form-group">
                <label>iCal URL</label>
                <input type="url" id="feed-edit-url" value="${escapeHtml(feed.url)}" required>
            </div>
            <div class="form-group">
                <label>Prefix <small style="font-weight:400;color:#888">(wordt voor elke entry gezet, bv. "Werk")</small></label>
                <input type="text" id="feed-edit-prefix" value="${escapeHtml(feed.prefix || "")}" placeholder="Optioneel, bv. Werk">
            </div>
            <div class="form-group">
                <label>Kleur op kalender</label>
                <input type="hidden" id="feed-edit-color" value="${escapeHtml(feed.color || "")}">
                <div class="color-swatches" id="feed-color-swatches">
                    ${buildColorSwatches(feed.color || "")}
                </div>
            </div>
            <div class="form-group">
                <label>Synchronisatie interval</label>
                <select id="feed-edit-interval">
                    <option value="15" ${interval === 15 ? "selected" : ""}>Elke 15 minuten</option>
                    <option value="60" ${interval === 60 ? "selected" : ""}>Elk uur</option>
                    <option value="1440" ${interval === 1440 ? "selected" : ""}>Dagelijks</option>
                </select>
            </div>
            <div class="form-group">
                <div class="toggle">
                    <div>
                        <div style="font-weight:600;font-size:14px">Tijden tonen</div>
                        <div style="color:#888;font-size:12px;margin-top:2px">Begin- en eindtijd tonen in de kalenderweergave op het dashboard (bv. 12:00-13:00)</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="feed-edit-show-times" ${showTimes ? "checked" : ""}>
                        <span class="slider"></span>
                    </label>
                </div>
            </div>
            <div class="form-group" id="feed-edit-hide-title-row" style="${showTimes ? "" : "display:none"}">
                <div class="toggle">
                    <div>
                        <div style="font-weight:600;font-size:14px">Omschrijving verbergen</div>
                        <div style="color:#888;font-size:12px;margin-top:2px">De naam van het agenda-item niet tonen, alleen de tijden</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="feed-edit-hide-title" ${hideTitle ? "checked" : ""}>
                        <span class="slider"></span>
                    </label>
                </div>
            </div>
            <div class="modal-actions">
                <button type="button" class="btn" onclick="hideModal()">Annuleren</button>
                <button type="submit" class="btn btn-primary">Opslaan</button>
            </div>
        </form>
    `);
    document.getElementById("feed-color-swatches").addEventListener("click", (e) => {
        const swatch = e.target.closest(".color-swatch");
        if (!swatch) return;
        document.querySelectorAll("#feed-color-swatches .color-swatch").forEach(s => s.classList.remove("selected"));
        swatch.classList.add("selected");
        document.getElementById("feed-edit-color").value = swatch.dataset.color;
    });
    document.getElementById("feed-edit-show-times").addEventListener("change", (e) => {
        document.getElementById("feed-edit-hide-title-row").style.display = e.target.checked ? "" : "none";
        if (!e.target.checked) {
            document.getElementById("feed-edit-hide-title").checked = false;
        }
    });
    document.getElementById("feed-edit-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const url = document.getElementById("feed-edit-url").value.trim();
        const label = document.getElementById("feed-edit-label").value.trim();
        const prefix = document.getElementById("feed-edit-prefix").value.trim();
        const color = document.getElementById("feed-edit-color").value;
        const syncInterval = parseInt(document.getElementById("feed-edit-interval").value);
        const showTimesVal = document.getElementById("feed-edit-show-times").checked;
        const hideTitleVal = document.getElementById("feed-edit-hide-title").checked;
        hideModal();
        await onSave({ url, label, prefix, color, sync_interval_minutes: syncInterval, show_times: showTimesVal, hide_title: hideTitleVal });
    });
}

function switchTab(tab) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("active", p.id === `tab-${tab}`));
    if (tab === "devices") {
        loadDevices().catch(() => {});
    }
}

function formatDeviceTime(iso) {
    if (!iso) return "Nog niet gebruikt";
    return new Date(iso).toLocaleString("nl-NL");
}

function deviceTypeLabel(type) {
    if (type === "mobile") return "Mobiele app";
    if (type === "dashboard") return "Dashboard";
    return type || "Onbekend";
}

function renderDevices(devices) {
    const list = document.getElementById("device-list");
    if (!list) return;
    if (!devices.length) {
        list.innerHTML = '<li class="feed-item"><span class="hint">Geen actieve apparaten.</span></li>';
        return;
    }
    list.innerHTML = devices.map(d => `
        <li class="feed-item" data-device-id="${escapeHtml(d.device_id)}">
            <div class="feed-info">
                <div class="feed-title">
                    ${escapeHtml(d.device_name)}
                    ${d.is_current ? '<span class="hint"> (dit apparaat)</span>' : ""}
                </div>
                <div class="feed-meta">
                    Type: ${escapeHtml(deviceTypeLabel(d.device_type))} &nbsp;|&nbsp;
                    Laatst gebruikt: ${formatDeviceTime(d.last_used_at)}
                </div>
            </div>
            <div class="feed-actions">
                <button class="btn btn-danger btn-small revoke-device" data-id="${escapeHtml(d.device_id)}"
                    ${d.is_current ? "disabled title=\"U kunt het huidige apparaat niet hier uitloggen\"" : ""}>
                    Uitloggen
                </button>
            </div>
        </li>
    `).join("");
}

async function loadDevices() {
    const devices = await api("/api/me/devices");
    renderDevices(devices);
}

function renderFeeds(feeds) {
    const list = document.getElementById("user-feed-list");
    if (!feeds.length) {
        list.innerHTML = '<li class="empty-state">Nog geen iCal agenda\'s</li>';
        return;
    }
    list.innerHTML = feeds.map(f => `
        <li>
            <div class="feed-info">
                <strong>${escapeHtml(f.label || f.url)}</strong>
                ${f.label ? `<div class="feed-url">${escapeHtml(f.url)}</div>` : ""}
                <div class="feed-meta">
                    Interval: ${formatInterval(f.sync_interval_minutes)} &nbsp;|&nbsp;
                    Laatste sync: ${formatChecked(f.last_synced_at)}
                    ${f.last_error ? `<span class="feed-error">Fout: ${escapeHtml(f.last_error)}</span>` : ""}
                </div>
            </div>
            <div class="feed-actions">
                <button class="btn btn-small sync-user-feed" data-id="${f.id}">Nu synchroniseren</button>
                <button class="btn btn-small edit-user-feed" data-id="${f.id}">Bewerken</button>
                <button class="btn btn-danger btn-small delete-user-feed" data-id="${f.id}">Verwijderen</button>
            </div>
        </li>
    `).join("");
}

async function loadMe() {
    me = await api("/api/me");
    document.getElementById("profile-name").value = me.name || "";
    document.getElementById("profile-email").value = me.email || "";
    renderFeeds(me.feeds || []);
}

document.addEventListener("DOMContentLoaded", async () => {
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });

    await loadMe();

    document.getElementById("profile-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("profile-name").value.trim();
        const email = document.getElementById("profile-email").value.trim();
        if (!name) return;
        try {
            me = await api("/api/me", { method: "PUT", body: JSON.stringify({ name, email: email || null }) });
            showToast("Opgeslagen", "success", 5000);
        } catch (err) {
            showToast(escapeHtml(err.message || "Opslaan mislukt"), "error", 5000);
        }
    });

    document.getElementById("password-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const p1 = document.getElementById("new-password").value;
        const p2 = document.getElementById("new-password-confirm").value;
        try {
            await api("/api/me/password", { method: "PUT", body: JSON.stringify({ password: p1, password_confirm: p2 }) });
            document.getElementById("new-password").value = "";
            document.getElementById("new-password-confirm").value = "";
            showToast("Wachtwoord opgeslagen", "success", 5000);
        } catch (err) {
            showToast(escapeHtml(err.message || "Opslaan mislukt"), "error", 5000);
        }
    });

    document.getElementById("btn-user-add-feed").addEventListener("click", async () => {
        const url = document.getElementById("user-feed-url").value.trim();
        const label = document.getElementById("user-feed-label").value.trim();
        if (!url) return;
        try {
            await api("/api/me/feeds", { method: "POST", body: JSON.stringify({ url, label }) });
            document.getElementById("user-feed-url").value = "";
            document.getElementById("user-feed-label").value = "";
            await loadMe();
        } catch (err) {
            showToast(escapeHtml(err.message || "Opslaan mislukt"), "error", 5000);
        }
    });

    document.getElementById("user-feed-list").addEventListener("click", async (e) => {
        const syncBtn = e.target.closest(".sync-user-feed");
        if (syncBtn) {
            const id = syncBtn.dataset.id;
            syncBtn.disabled = true;
            syncBtn.textContent = "Bezig…";
            try {
                const res = await api(`/api/me/feeds/${id}/sync`, { method: "POST" });
                await loadMe();
                showToast(`Gesynchroniseerd — ${res.imported} item(s) geïmporteerd`, "success", 5000);
            } catch (err) {
                showToast(escapeHtml(err.message || "Synchronisatie mislukt"), "error", 5000);
                syncBtn.disabled = false;
                syncBtn.textContent = "Nu synchroniseren";
            }
            return;
        }

        const editBtn = e.target.closest(".edit-user-feed");
        if (editBtn) {
            const id = editBtn.dataset.id;
            const feed = (me.feeds || []).find(f => String(f.id) === String(id));
            if (!feed) return;
            showFeedEditModal(feed, async (payload) => {
                try {
                    await api(`/api/me/feeds/${id}`, {
                        method: "PUT",
                        body: JSON.stringify(payload),
                    });
                    await loadMe();
                    showToast("Opgeslagen", "success", 5000);
                } catch (err) {
                    showToast(escapeHtml(err.message || "Opslaan mislukt"), "error", 5000);
                }
            });
            return;
        }

        const deleteBtn = e.target.closest(".delete-user-feed");
        if (deleteBtn) {
            const id = deleteBtn.dataset.id;
            if (!confirm("iCal adres verwijderen?")) return;
            try {
                const res = await api(`/api/me/feeds/${id}`, { method: "DELETE" });
                await loadMe();
                if (res?.validation_warning) {
                    showToast(`Verwijderd. Let op: test faalde: ${escapeHtml(res.validation_warning)}`, "error", 5000);
                } else {
                    showToast("Verwijderd", "success", 5000);
                }
            } catch (err) {
                showToast(escapeHtml(err.message || "Verwijderen mislukt"), "error", 5000);
            }
        }
    });

    document.getElementById("device-list")?.addEventListener("click", async (e) => {
        const btn = e.target.closest(".revoke-device");
        if (!btn || btn.disabled) return;
        const deviceId = btn.dataset.id;
        if (!deviceId || !confirm("Dit apparaat uitloggen?")) return;
        try {
            await api(`/api/me/devices/${encodeURIComponent(deviceId)}`, { method: "DELETE" });
            await loadDevices();
            showToast("Apparaat uitgelogd", "success", 5000);
        } catch (err) {
            showToast(escapeHtml(err.message || "Uitloggen mislukt"), "error", 5000);
        }
    });
});

