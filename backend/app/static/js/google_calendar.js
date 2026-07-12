/**
 * Shared Google Calendar UI logic for profile and admin user detail pages.
 * Requires: escapeHtml(), showToast(), api() – provided by the host page.
 *
 * Usage:
 *   initGoogleCalendarSection({ baseUrl, returnTo })
 *
 * baseUrl  – API base path: "/api/me/google" or "/api/admin/users/{id}/google"
 * returnTo – URL to return to after OAuth (e.g. "/profile" or "/admin/user/5")
 */

const GOOGLE_COLOR_MAP = {
    "1":  { name: "Lavendel",  hex: "#7986CB" },
    "2":  { name: "Salie",     hex: "#33B679" },
    "3":  { name: "Druif",     hex: "#8E24AA" },
    "4":  { name: "Flamingo",  hex: "#E67C73" },
    "5":  { name: "Banaan",    hex: "#F6BF26" },
    "6":  { name: "Mandarijn", hex: "#F4511E" },
    "7":  { name: "Pauw",      hex: "#039BE5" },
    "8":  { name: "Grafiet",   hex: "#616161" },
    "9":  { name: "Bosbes",    hex: "#3F51B5" },
    "10": { name: "Basilicum", hex: "#0B8043" },
    "11": { name: "Tomaat",    hex: "#D50000" },
};

function buildColorFilterSwatches(selectedIds, onToggle) {
    const wrap = document.createElement("div");
    wrap.className = "gcal-color-filters";

    const noneBtn = document.createElement("button");
    noneBtn.type = "button";
    noneBtn.className = "gcal-color-swatch swatch-none" + (!selectedIds.length ? " selected" : "");
    noneBtn.title = "Alle kleuren";
    noneBtn.textContent = "Alles";
    noneBtn.addEventListener("click", () => {
        selectedIds.length = 0;
        wrap.querySelectorAll(".gcal-color-swatch").forEach(b => b.classList.remove("selected"));
        noneBtn.classList.add("selected");
        onToggle([]);
    });
    wrap.appendChild(noneBtn);

    for (const [id, info] of Object.entries(GOOGLE_COLOR_MAP)) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "gcal-color-swatch" + (selectedIds.includes(id) ? " selected" : "");
        btn.title = info.name;
        btn.style.background = info.hex;
        btn.dataset.colorId = id;
        btn.addEventListener("click", () => {
            const idx = selectedIds.indexOf(id);
            if (idx >= 0) {
                selectedIds.splice(idx, 1);
                btn.classList.remove("selected");
            } else {
                selectedIds.push(id);
                btn.classList.add("selected");
            }
            noneBtn.classList.toggle("selected", selectedIds.length === 0);
            onToggle([...selectedIds]);
        });
        wrap.appendChild(btn);
    }

    return wrap;
}

function renderGoogleFeeds(feeds, baseUrl, onChanged) {
    const list = document.getElementById("google-feed-list");
    if (!feeds.length) {
        list.innerHTML = '<li class="empty-state">Nog geen Google agenda\'s gekoppeld</li>';
        return;
    }
    list.innerHTML = "";

    feeds.forEach(feed => {
        const li = document.createElement("li");
        li.dataset.id = feed.id;

        const colorIds = [...(feed.color_filters || [])];
        const colorLabel = colorIds.length
            ? colorIds.map(id => GOOGLE_COLOR_MAP[id]?.name || id).join(", ")
            : "Alle kleuren";

        li.innerHTML = `
            <div class="feed-info">
                <strong>${escapeHtml(feed.calendar_name || feed.google_calendar_id)}</strong>
                <div class="feed-meta">
                    Kleurfilter: <span class="gcal-filter-label">${escapeHtml(colorLabel)}</span>
                    &nbsp;|&nbsp; Laatste sync: ${feed.last_synced_at ? new Date(feed.last_synced_at).toLocaleString("nl-NL") : "Nog niet"}
                    ${feed.last_error ? `<span class="feed-error"> Fout: ${escapeHtml(feed.last_error)}</span>` : ""}
                </div>
                <div class="gcal-filter-row"></div>
            </div>
            <div class="feed-actions">
                <label class="switch" title="${feed.enabled ? "Uitschakelen" : "Inschakelen"}">
                    <input type="checkbox" class="gcal-enabled-toggle" ${feed.enabled ? "checked" : ""}>
                    <span class="slider"></span>
                </label>
                <button class="btn btn-secondary btn-small gcal-sync-btn" title="Nu synchroniseren">↻ Nu</button>
                <button class="btn btn-danger btn-small gcal-delete-btn">Verwijderen</button>
            </div>
        `;

        const filterRow = li.querySelector(".gcal-filter-row");
        const swatches = buildColorFilterSwatches(colorIds, async (newIds) => {
            try {
                const updated = await api(`${baseUrl}/feeds/${feed.id}`, {
                    method: "PUT",
                    body: JSON.stringify({ color_filters: newIds }),
                });
                const label = li.querySelector(".gcal-filter-label");
                label.textContent = newIds.length
                    ? newIds.map(id => GOOGLE_COLOR_MAP[id]?.name || id).join(", ")
                    : "Alle kleuren";
                if (updated.last_synced_at) {
                    const lastSyncEl = li.querySelector(".feed-meta");
                    const ts = new Date(updated.last_synced_at).toLocaleString("nl-NL");
                    lastSyncEl.innerHTML = lastSyncEl.innerHTML.replace(
                        /Laatste sync:[^|]*/,
                        `Laatste sync: ${ts} `
                    );
                }
                showToast("Kleurfilter toegepast", "success", 3000);
            } catch (err) {
                showToast("Opslaan mislukt: " + escapeHtml(err.message), "error");
            }
        });
        filterRow.appendChild(swatches);

        li.querySelector(".gcal-enabled-toggle").addEventListener("change", async (e) => {
            try {
                await api(`${baseUrl}/feeds/${feed.id}`, {
                    method: "PUT",
                    body: JSON.stringify({ enabled: e.target.checked }),
                });
            } catch (err) {
                e.target.checked = !e.target.checked;
                showToast("Opslaan mislukt: " + escapeHtml(err.message), "error");
            }
        });

        li.querySelector(".gcal-sync-btn").addEventListener("click", async (e) => {
            const btn = e.currentTarget;
            const original = btn.textContent;
            btn.disabled = true;
            btn.textContent = "Bezig…";
            try {
                const updated = await api(`${baseUrl}/feeds/${feed.id}/sync`, { method: "POST" });
                const lastSyncEl = li.querySelector(".feed-meta");
                if (lastSyncEl && updated.last_synced_at) {
                    const ts = new Date(updated.last_synced_at).toLocaleString("nl-NL");
                    lastSyncEl.innerHTML = lastSyncEl.innerHTML.replace(
                        /Laatste sync:[^|]*/,
                        `Laatste sync: ${ts} `
                    );
                }
                showToast("Synchronisatie voltooid", "success", 3000);
            } catch (err) {
                showToast("Synchronisatie mislukt: " + escapeHtml(err.message), "error");
            } finally {
                btn.disabled = false;
                btn.textContent = original;
            }
        });

        li.querySelector(".gcal-delete-btn").addEventListener("click", async () => {
            if (!confirm(`Agenda '${feed.calendar_name || feed.google_calendar_id}' ontkoppelen?`)) return;
            try {
                await api(`${baseUrl}/feeds/${feed.id}`, { method: "DELETE" });
                li.remove();
                onChanged();
            } catch (err) {
                showToast("Verwijderen mislukt: " + escapeHtml(err.message), "error");
            }
        });

        list.appendChild(li);
    });
}

function renderAvailableCalendars(cals, existingFeeds, baseUrl, onAdded) {
    const container = document.getElementById("google-available-list");
    const loadBtn = document.getElementById("btn-load-gcals");

    const subscribedIds = new Set(existingFeeds.map(f => f.google_calendar_id));

    if (!cals.length) {
        container.innerHTML = '<p class="hint">Geen agenda\'s gevonden in dit Google-account.</p>';
        return;
    }

    container.innerHTML = "";
    cals.forEach(cal => {
        const row = document.createElement("div");
        row.className = "gcal-available-item";
        const isLinked = subscribedIds.has(cal.id);

        row.innerHTML = `
            <span class="gcal-cal-dot" style="background:${escapeHtml(cal.backgroundColor || "#888")}"></span>
            <span class="gcal-cal-name">${escapeHtml(cal.summary || cal.id)}</span>
            <button class="btn btn-small ${isLinked ? "btn-secondary" : "btn-primary"} gcal-add-btn"
                    ${isLinked ? "disabled" : ""}>
                ${isLinked ? "Al gekoppeld" : "Koppelen"}
            </button>
        `;

        if (!isLinked) {
            row.querySelector(".gcal-add-btn").addEventListener("click", async () => {
                try {
                    const feed = await api(`${baseUrl}/feeds`, {
                        method: "POST",
                        body: JSON.stringify({
                            google_calendar_id: cal.id,
                            calendar_name: cal.summary || cal.id,
                            calendar_color: cal.backgroundColor || null,
                        }),
                    });
                    row.querySelector(".gcal-add-btn").disabled = true;
                    row.querySelector(".gcal-add-btn").textContent = "Al gekoppeld";
                    row.querySelector(".gcal-add-btn").className = "btn btn-small btn-secondary gcal-add-btn";
                    onAdded(feed);
                } catch (err) {
                    showToast("Koppelen mislukt: " + escapeHtml(err.message), "error");
                }
            });
        }

        container.appendChild(row);
    });

    if (loadBtn) {
        container.prepend(loadBtn);
    }
}

async function initGoogleCalendarSection({ baseUrl, returnTo, authUrlBase }) {
    const linkedInfo = document.getElementById("google-linked-info");
    const notLinkedInfo = document.getElementById("google-not-linked-info");
    const calSection = document.getElementById("google-calendars-section");
    const emailEl = document.getElementById("google-linked-email");

    const params = new URLSearchParams(location.search);
    if (params.get("google_linked") === "1") {
        showToast("Google account succesvol gekoppeld!", "success", 5000);
        history.replaceState({}, "", location.pathname + (location.hash || ""));
    }
    if (params.get("google_error")) {
        const msg = {
            no_config: "Google Calendar API is niet geconfigureerd.",
            invalid_callback: "Ongeldige OAuth callback.",
            state_mismatch: "Beveiligingscontrole mislukt. Probeer opnieuw.",
            exchange_failed: "Koppeling mislukt. Controleer de API-instellingen.",
        }[params.get("google_error")] || "Koppeling mislukt: " + params.get("google_error");
        showToast(msg, "error", 8000);
        history.replaceState({}, "", location.pathname + (location.hash || ""));
    }

    let existingFeeds = [];

    async function loadStatus() {
        const status = await api(`${baseUrl}/status`);
        if (status.linked) {
            linkedInfo.classList.remove("hidden");
            notLinkedInfo.classList.add("hidden");
            emailEl.textContent = status.google_email || "onbekend";
            calSection.classList.remove("hidden");
            existingFeeds = await api(`${baseUrl}/feeds`);
            renderGoogleFeeds(existingFeeds, baseUrl, loadStatus);
        } else {
            linkedInfo.classList.add("hidden");
            notLinkedInfo.classList.remove("hidden");
            calSection.classList.add("hidden");
        }
    }

    await loadStatus();

    document.getElementById("btn-google-link").addEventListener("click", async () => {
        try {
            const resp = await api(`${authUrlBase}?return_to=${encodeURIComponent(returnTo)}`);
            location.href = resp.auth_url;
        } catch (err) {
            showToast("Ophalen autorisatie-URL mislukt: " + escapeHtml(err.message), "error");
        }
    });

    document.getElementById("btn-google-unlink").addEventListener("click", async () => {
        if (!confirm("Google account loskoppelen? Alle gesynchroniseerde agenda-items blijven bestaan.")) return;
        try {
            await api(`${baseUrl}/auth`, { method: "DELETE" });
            await loadStatus();
            showToast("Google account ontkoppeld", "success", 4000);
        } catch (err) {
            showToast("Ontkoppelen mislukt: " + escapeHtml(err.message), "error");
        }
    });

    document.getElementById("btn-load-gcals").addEventListener("click", async () => {
        const btn = document.getElementById("btn-load-gcals");
        btn.disabled = true;
        try {
            const cals = await api(`${baseUrl}/calendars`);
            existingFeeds = await api(`${baseUrl}/feeds`);
            renderAvailableCalendars(cals, existingFeeds, baseUrl, (newFeed) => {
                existingFeeds.push(newFeed);
                renderGoogleFeeds(existingFeeds, baseUrl, loadStatus);
                showToast(`Agenda '${newFeed.calendar_name}' gekoppeld`, "success", 4000);
            });
        } catch (err) {
            showToast("Ophalen mislukt: " + escapeHtml(err.message), "error");
            btn.disabled = false;
        }
    });
}
