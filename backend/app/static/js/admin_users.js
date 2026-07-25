let me = null;
let users = [];
let dragFromIndex = null;

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
}

function formatApiError(err) {
    if (!err) return "Onbekende fout";
    const msg = err.message || String(err);
    if (msg === "[object Object]") return "Verzoek mislukt";
    return msg;
}

function userColorStyle(label) {
    if (typeof colorSwatchStyle === "function") {
        return colorSwatchStyle(label);
    }
    if (typeof COLOR_SWATCHES !== "undefined") {
        const swatch = COLOR_SWATCHES.find((c) => c.label === label);
        if (swatch) return `background:${swatch.bg};color:${swatch.text}`;
    }
    return "background:#EBF8FF;color:#2B6CB0";
}

function userColorLabel(value) {
    if (typeof normalizeColorLabel === "function") {
        return normalizeColorLabel(value) || "blauw";
    }
    return value || "blauw";
}

function render() {
    const list = document.getElementById("admin-user-list");
    if (!list) return;
    if (!users.length) {
        list.innerHTML = '<li class="empty-state">Nog geen gebruikers</li>';
        return;
    }

    list.innerHTML = users.map((u, index) => {
        const color = userColorLabel(u.profile_color);
        const style = userColorStyle(color);
        return `
        <li class="user-row" draggable="true" data-id="${u.id}" data-index="${index}">
            <span class="drag-handle" title="Sleep om te verplaatsen" aria-hidden="true">⋮⋮</span>
            <span class="user-color-dot" style="${style}" title="${escapeHtml(color)}"></span>
            <div class="user-cols">
                <span class="user-col-name">${escapeHtml(u.name)}</span>
                <span class="user-col-username">${escapeHtml(u.username || "")}</span>
            </div>
            <div class="person-actions">
                <a class="btn btn-small" href="/admin/user/${u.id}">Bewerken</a>
                <button class="btn btn-danger btn-small delete-user" data-id="${u.id}" ${me?.id === u.id ? "disabled" : ""}>
                    Verwijderen
                </button>
            </div>
        </li>`;
    }).join("");
}

async function persistOrder() {
    const ids = users.map((u) => u.id);
    await api("/api/admin/users/reorder", {
        method: "PUT",
        body: JSON.stringify({ ids }),
    });
}

async function refresh() {
    me = await api("/api/me");
    users = await api("/api/admin/users");
    render();
}

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await refresh();
    } catch (err) {
        const message = formatApiError(err);
        showToast(escapeHtml(message), "error", 8000);
        // Only leave the page when auth/admin access is denied — not on render/network glitches
        if (/niet ingelogd|admin rechten|401|403/i.test(message)) {
            window.location.href = "/dashboard";
        }
        return;
    }

    const list = document.getElementById("admin-user-list");
    if (!list) return;

    list.addEventListener("click", async (e) => {
        const delBtn = e.target.closest(".delete-user");
        if (delBtn) {
            const id = delBtn.dataset.id;
            if (String(me.id) === String(id)) return;
            if (!confirm("Gebruiker verwijderen?")) return;
            try {
                await api(`/api/admin/users/${id}`, { method: "DELETE" });
                await refresh();
                showToast("Verwijderd", "success", 5000);
            } catch (err) {
                showToast(escapeHtml(formatApiError(err)), "error", 5000);
            }
        }
    });

    list.addEventListener("dragstart", (e) => {
        const row = e.target.closest(".user-row");
        if (!row) return;
        dragFromIndex = parseInt(row.dataset.index, 10);
        row.classList.add("dragging");
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", row.dataset.id);
    });

    list.addEventListener("dragend", (e) => {
        const row = e.target.closest(".user-row");
        if (row) row.classList.remove("dragging");
        list.querySelectorAll(".user-row").forEach((el) => el.classList.remove("drag-over"));
        dragFromIndex = null;
    });

    list.addEventListener("dragover", (e) => {
        e.preventDefault();
        const row = e.target.closest(".user-row");
        if (!row) return;
        list.querySelectorAll(".user-row").forEach((el) => el.classList.remove("drag-over"));
        row.classList.add("drag-over");
        e.dataTransfer.dropEffect = "move";
    });

    list.addEventListener("drop", async (e) => {
        e.preventDefault();
        const row = e.target.closest(".user-row");
        list.querySelectorAll(".user-row").forEach((el) => el.classList.remove("drag-over"));
        if (!row || dragFromIndex === null) return;
        const toIndex = parseInt(row.dataset.index, 10);
        if (Number.isNaN(toIndex) || toIndex === dragFromIndex) return;
        const [moved] = users.splice(dragFromIndex, 1);
        users.splice(toIndex, 0, moved);
        render();
        try {
            await persistOrder();
            showToast("Volgorde opgeslagen", "success", 3000);
        } catch (err) {
            showToast(escapeHtml(formatApiError(err)), "error", 5000);
            await refresh();
        }
    });
});
