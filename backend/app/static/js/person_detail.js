let personData = null;

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatSyncTime(iso) {
    if (!iso) return "Nog niet gesynchroniseerd";
    const d = new Date(iso);
    return d.toLocaleString("nl-NL");
}

function togglePasswordFields() {
    const canLogin = document.getElementById("can-login").checked;
    const fields = document.getElementById("password-fields");
    const hint = document.getElementById("password-hint");

    fields.classList.toggle("hidden", !canLogin);
    if (canLogin) {
        hint.textContent = personData?.has_password
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
                    Laatste sync: ${formatSyncTime(feed.last_synced_at)}
                    ${feed.last_error ? `<span class="feed-error">Fout: ${escapeHtml(feed.last_error)}</span>` : ""}
                </div>
            </div>
            <div class="feed-actions">
                <button class="btn btn-small sync-feed" data-id="${feed.id}">Nu syncen</button>
                <button class="btn btn-danger btn-small delete-feed" data-id="${feed.id}">Verwijderen</button>
            </div>
        </li>
    `).join("");
}

async function loadPerson() {
    personData = await api(`/api/persons/${PERSON_ID}`);
    document.getElementById("person-title").textContent = personData.name;
    document.getElementById("person-name").value = personData.name;
    document.getElementById("can-login").checked = personData.can_login;
    togglePasswordFields();
    renderFeeds(personData.feeds || []);
}

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadPerson();
    } catch (err) {
        alert(err.message || "Persoon niet gevonden");
        window.location.href = "/settings";
        return;
    }

    document.getElementById("can-login").addEventListener("change", togglePasswordFields);

    document.getElementById("person-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("person-name").value.trim();
        const canLogin = document.getElementById("can-login").checked;
        const password = document.getElementById("password").value;
        const passwordConfirm = document.getElementById("password-confirm").value;

        if (!name) return;

        try {
            personData = await api(`/api/persons/${PERSON_ID}`, {
                method: "PUT",
                body: JSON.stringify({
                    name,
                    can_login: canLogin,
                    password: password || null,
                    password_confirm: passwordConfirm || null,
                }),
            });
            document.getElementById("person-title").textContent = personData.name;
            document.getElementById("password").value = "";
            document.getElementById("password-confirm").value = "";
            togglePasswordFields();
            alert("Opgeslagen");
        } catch (err) {
            alert(err.message);
        }
    });

    document.getElementById("btn-add-feed").addEventListener("click", async () => {
        const url = document.getElementById("feed-url").value.trim();
        const label = document.getElementById("feed-label").value.trim();
        if (!url) return;

        try {
            const feed = await api(`/api/persons/${PERSON_ID}/feeds`, {
                method: "POST",
                body: JSON.stringify({ url, label }),
            });
            document.getElementById("feed-url").value = "";
            document.getElementById("feed-label").value = "";
            await loadPerson();
            if (feed.sync_warning) {
                alert(`Kalender toegevoegd, maar sync mislukt: ${feed.sync_warning}`);
            }
        } catch (err) {
            alert(err.message);
        }
    });

    document.getElementById("feed-list").addEventListener("click", async (e) => {
        const syncBtn = e.target.closest(".sync-feed");
        if (syncBtn) {
            const feedId = syncBtn.dataset.id;
            syncBtn.disabled = true;
            try {
                await api(`/api/persons/${PERSON_ID}/feeds/${feedId}/sync`, { method: "POST" });
                await loadPerson();
            } catch (err) {
                alert(err.message);
                await loadPerson();
            } finally {
                syncBtn.disabled = false;
            }
            return;
        }

        const deleteBtn = e.target.closest(".delete-feed");
        if (deleteBtn) {
            const feedId = deleteBtn.dataset.id;
            if (!confirm("Externe kalender en geïmporteerde items verwijderen?")) return;
            try {
                await api(`/api/persons/${PERSON_ID}/feeds/${feedId}`, { method: "DELETE" });
                await loadPerson();
            } catch (err) {
                alert(err.message);
            }
        }
    });
});
