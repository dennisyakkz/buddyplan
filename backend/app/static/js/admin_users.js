let me = null;
let users = [];

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function render() {
    const list = document.getElementById("admin-user-list");
    if (!users.length) {
        list.innerHTML = '<li class="empty-state">Nog geen gebruikers</li>';
        return;
    }

    list.innerHTML = users.map(u => `
        <li class="user-row">
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
        </li>
    `).join("");
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
        showToast(escapeHtml(err.message || "Geen toegang"), "error", 5000);
        window.location.href = "/tasks";
        return;
    }

    document.getElementById("admin-user-list").addEventListener("click", async (e) => {
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
                showToast(escapeHtml(err.message || "Verwijderen mislukt"), "error", 5000);
            }
        }
    });
});

