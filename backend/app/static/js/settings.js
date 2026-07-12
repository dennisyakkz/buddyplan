async function loadPersons() {
    return api("/api/persons");
}

function renderPersonList(persons) {
    const list = document.getElementById("person-list");
    if (persons.length === 0) {
        list.innerHTML = '<li class="empty-state">Nog geen personen toegevoegd</li>';
        return;
    }
    list.innerHTML = persons.map(p => `
        <li>
            <span>${escapeHtml(p.name)}</span>
            <div class="person-actions">
                <a href="/settings/person/${p.id}" class="btn btn-small">Bewerken</a>
                <button class="btn btn-danger btn-small delete-person" data-id="${p.id}">Verwijderen</button>
            </div>
        </li>
    `).join("");
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener("DOMContentLoaded", async () => {
    async function refresh() {
        const persons = await loadPersons();
        renderPersonList(persons);
    }

    await refresh();

    document.getElementById("btn-add-person").addEventListener("click", async () => {
        const input = document.getElementById("person-name");
        const name = input.value.trim();
        if (!name) return;
        await api("/api/persons", { method: "POST", body: JSON.stringify({ name }) });
        input.value = "";
        await refresh();
    });

    document.getElementById("person-name").addEventListener("keydown", (e) => {
        if (e.key === "Enter") document.getElementById("btn-add-person").click();
    });

    document.getElementById("person-list").addEventListener("click", async (e) => {
        if (e.target.closest(".delete-person")) {
            const id = e.target.closest(".delete-person").dataset.id;
            if (confirm("Persoon en alle agenda-items verwijderen?")) {
                await api(`/api/persons/${id}`, { method: "DELETE" });
                await refresh();
            }
        }
    });
});
