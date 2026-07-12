let userData = null;
let allUsers = [];

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function switchTab(tab) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("active", p.id === `tab-${tab}`));
    if (tab === "tasks") {
        loadManagers().catch(() => {});
    }
    if (tab === "devices" && USER_ID) {
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
                <div class="feed-title">${escapeHtml(d.device_name)}</div>
                <div class="feed-meta">
                    Type: ${escapeHtml(deviceTypeLabel(d.device_type))} &nbsp;|&nbsp;
                    Laatst gebruikt: ${formatDeviceTime(d.last_used_at)}
                </div>
            </div>
            <div class="feed-actions">
                <button class="btn btn-danger btn-small revoke-device" data-id="${escapeHtml(d.device_id)}">
                    Uitloggen
                </button>
            </div>
        </li>
    `).join("");
}

async function loadDevices() {
    const devices = await api(`/api/admin/users/${USER_ID}/devices`);
    renderDevices(devices);
}

function formatSyncTime(iso) {
    if (!iso) return "Nog niet gesynchroniseerd";
    return new Date(iso).toLocaleString("nl-NL");
}

function formatInterval(minutes) {
    if (minutes === 15) return "Elke 15 minuten";
    if (minutes === 1440) return "Dagelijks";
    return "Elk uur";
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

function togglePasswordFields() {
    const canLogin = document.getElementById("user-can-login").checked;
    const fields = document.getElementById("user-password-fields");
    const hint = document.getElementById("user-password-hint");
    fields.classList.toggle("hidden", !canLogin);
    if (canLogin) {
        hint.textContent = userData?.has_password
            ? "Laat leeg om het huidige wachtwoord te behouden."
            : "Stel een wachtwoord in om inloggen mogelijk te maken.";
    }
}

function renderFeeds(feeds) {
    const list = document.getElementById("feed-list");
    if (!feeds.length) {
        list.innerHTML = '<li class="empty-state">Nog geen externe kalenders</li>';
        return;
    }

    list.innerHTML = feeds.map(feed => `
        <li>
            <div class="feed-info">
                <strong>${escapeHtml(feed.label || feed.url)}</strong>
                ${feed.label ? `<div class="feed-url">${escapeHtml(feed.url)}</div>` : ""}
                <div class="feed-meta">
                    Interval: ${formatInterval(feed.sync_interval_minutes)} &nbsp;|&nbsp;
                    Laatste sync: ${formatSyncTime(feed.last_synced_at)}
                    ${feed.last_error ? `<span class="feed-error">Fout: ${escapeHtml(feed.last_error)}</span>` : ""}
                </div>
            </div>
            <div class="feed-actions">
                <button class="btn btn-small sync-feed" data-id="${feed.id}">Nu synchroniseren</button>
                <button class="btn btn-small edit-feed" data-id="${feed.id}">Bewerken</button>
                <button class="btn btn-danger btn-small delete-feed" data-id="${feed.id}">Verwijderen</button>
            </div>
        </li>
    `).join("");
}

async function loadUser() {
    userData = await api(`/api/admin/users/${USER_ID}`);
    document.getElementById("user-title").textContent = userData.name;
    document.getElementById("user-username").value = userData.username || "";
    document.getElementById("user-name").value = userData.name || "";
    document.getElementById("user-email").value = userData.email || "";
    document.getElementById("user-can-login").checked = !!userData.can_login;
    document.getElementById("user-is-admin").checked = !!userData.is_admin;
    togglePasswordFields();
    renderFeeds(userData.feeds || []);

    document.getElementById("tasks-enabled").checked = !!userData.tasks_enabled;
}

function renderUserChecks(containerId, selectedIds) {
    const selected = new Set(selectedIds || []);
    document.getElementById(containerId).innerHTML = allUsers.map(u => `
        <label>
            <input type="checkbox" value="${u.id}" ${selected.has(u.id) ? "checked" : ""}>
            ${escapeHtml(u.name)} (${escapeHtml(u.username || "")})
        </label>
    `).join("");
}

async function loadManagers() {
    allUsers = await api("/api/admin/users");

    renderUserChecks("agenda-managers-list", userData.agenda_manager_ids || []);

    const block = document.getElementById("task-managers-block");
    const enabled = document.getElementById("tasks-enabled").checked;
    block.classList.toggle("hidden", !enabled);
    if (!enabled) {
        document.getElementById("task-managers-list").innerHTML = "";
        return;
    }
    renderUserChecks("task-managers-list", userData.task_manager_ids || []);
}

document.addEventListener("DOMContentLoaded", async () => {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.addEventListener("click", () => switchTab(btn.dataset.tab)));
    document.getElementById("user-can-login").addEventListener("change", togglePasswordFields);
    document.getElementById("tasks-enabled").addEventListener("change", () => loadManagers());

    if (USER_ID !== null) {
        try {
            await loadUser();
        } catch (err) {
            showToast(escapeHtml(err.message || "Gebruiker niet gevonden"), "error", 5000);
            window.location.href = "/admin";
            return;
        }
    } else {
        userData = { has_password: false, feeds: [], tasks_enabled: false, task_manager_ids: [], agenda_manager_ids: [] };
        document.getElementById("user-title").textContent = "Nieuwe gebruiker";
        togglePasswordFields();
        renderFeeds([]);
    }

    document.getElementById("user-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("user-username").value.trim();
        const name = document.getElementById("user-name").value.trim();
        const email = document.getElementById("user-email").value.trim();
        const canLogin = document.getElementById("user-can-login").checked;
        const isAdmin = document.getElementById("user-is-admin").checked;
        const password = document.getElementById("user-password").value;
        const passwordConfirm = document.getElementById("user-password-confirm").value;

        if (!username || !name) return;

        const payload = {
            username,
            name,
            email: email || null,
            can_login: canLogin,
            is_admin: isAdmin,
            password: password || null,
            password_confirm: passwordConfirm || null,
        };

        try {
            if (USER_ID === null) {
                const created = await api("/api/admin/users", { method: "POST", body: JSON.stringify(payload) });
                window.location.href = `/admin/user/${created.id}`;
                return;
            }
            await api(`/api/admin/users/${USER_ID}`, { method: "PUT", body: JSON.stringify(payload) });
            document.getElementById("user-password").value = "";
            document.getElementById("user-password-confirm").value = "";
            await loadUser();
            showToast("Opgeslagen", "success", 5000);
        } catch (err) {
            showToast(escapeHtml(err.message || "Opslaan mislukt"), "error", 5000);
        }
    });

    document.getElementById("btn-add-feed").addEventListener("click", async () => {
        if (USER_ID === null) {
            showToast("Sla eerst de gebruiker op.", "error", 5000);
            return;
        }
        const url = document.getElementById("feed-url").value.trim();
        const label = document.getElementById("feed-label").value.trim();
        if (!url) return;
        try {
            await api(`/api/admin/users/${USER_ID}/feeds`, { method: "POST", body: JSON.stringify({ url, label }) });
            document.getElementById("feed-url").value = "";
            document.getElementById("feed-label").value = "";
            await loadUser();
        } catch (err) {
            showToast(escapeHtml(err.message || "Opslaan mislukt"), "error", 5000);
        }
    });

    document.getElementById("btn-save-agenda-managers").addEventListener("click", async () => {
        if (USER_ID === null) {
            showToast("Sla eerst de gebruiker op.", "error", 5000);
            return;
        }
        const ids = Array.from(document.querySelectorAll("#agenda-managers-list input[type=checkbox]:checked"))
            .map(i => parseInt(i.value));
        try {
            userData = await api(`/api/admin/users/${USER_ID}/agenda-managers`, {
                method: "PUT",
                body: JSON.stringify({ manager_ids: ids }),
            });
            await loadUser();
            showToast("Opgeslagen", "success", 5000);
        } catch (err) {
            showToast(escapeHtml(err.message || "Opslaan mislukt"), "error", 5000);
        }
    });

    document.getElementById("btn-save-task-managers").addEventListener("click", async () => {
        if (USER_ID === null) {
            showToast("Sla eerst de gebruiker op.", "error", 5000);
            return;
        }
        const enabled = document.getElementById("tasks-enabled").checked;
        const ids = Array.from(document.querySelectorAll("#task-managers-list input[type=checkbox]:checked"))
            .map(i => parseInt(i.value));
        try {
            userData = await api(`/api/admin/users/${USER_ID}/task-managers`, {
                method: "PUT",
                body: JSON.stringify({ tasks_enabled: enabled, manager_ids: ids }),
            });
            await loadUser();
            showToast("Opgeslagen", "success", 5000);
        } catch (err) {
            showToast(escapeHtml(err.message || "Opslaan mislukt"), "error", 5000);
        }
    });

    document.getElementById("feed-list").addEventListener("click", async (e) => {
        const syncBtn = e.target.closest(".sync-feed");
        if (syncBtn) {
            const id = syncBtn.dataset.id;
            syncBtn.disabled = true;
            syncBtn.textContent = "Bezig…";
            try {
                const res = await api(`/api/admin/users/${USER_ID}/feeds/${id}/sync`, { method: "POST" });
                await loadUser();
                showToast(`Gesynchroniseerd — ${res.imported} item(s) geïmporteerd`, "success", 5000);
            } catch (err) {
                showToast(escapeHtml(err.message || "Synchronisatie mislukt"), "error", 5000);
                syncBtn.disabled = false;
                syncBtn.textContent = "Nu synchroniseren";
            }
            return;
        }

        const editBtn = e.target.closest(".edit-feed");
        if (editBtn) {
            const id = editBtn.dataset.id;
            const feed = (userData.feeds || []).find(f => String(f.id) === String(id));
            if (!feed) return;
            showFeedEditModal(feed, async (payload) => {
                try {
                    await api(`/api/admin/users/${USER_ID}/feeds/${id}`, {
                        method: "PUT",
                        body: JSON.stringify(payload),
                    });
                    await loadUser();
                    showToast("Opgeslagen", "success", 5000);
                } catch (err) {
                    showToast(escapeHtml(err.message || "Opslaan mislukt"), "error", 5000);
                }
            });
            return;
        }

        const deleteBtn = e.target.closest(".delete-feed");
        if (deleteBtn) {
            const id = deleteBtn.dataset.id;
            if (!confirm("iCal adres verwijderen?")) return;
            try {
                const res = await api(`/api/admin/users/${USER_ID}/feeds/${id}`, { method: "DELETE" });
                await loadUser();
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
        if (!btn) return;
        const deviceId = btn.dataset.id;
        if (!deviceId || !confirm("Dit apparaat uitloggen?")) return;
        try {
            await api(
                `/api/admin/users/${USER_ID}/devices/${encodeURIComponent(deviceId)}`,
                { method: "DELETE" },
            );
            await loadDevices();
            showToast("Apparaat uitgelogd", "success", 5000);
        } catch (err) {
            showToast(escapeHtml(err.message || "Uitloggen mislukt"), "error", 5000);
        }
    });
});

