let calendar;
let currentPersonId = null;
let canManage = false;

async function loadPersons() {
    return api("/api/persons");
}

async function loadAgendaForDate(date) {
    if (!currentPersonId) return [];
    return api(`/api/agenda?person_id=${currentPersonId}&date=${toISODate(date)}`);
}

function renderAgendaCard(item) {
    const disabled = canManage ? "" : "disabled-actions";
    return `
        <div class="agenda-card ${disabled}" data-id="${item.id}">
            <span>${escapeHtml(item.title)}</span>
            <div>
                <button class="btn-small edit-agenda" data-id="${item.id}" ${canManage ? "" : "disabled"}>✎</button>
                <button class="btn-small delete-agenda" data-id="${item.id}" ${canManage ? "" : "disabled"}>✕</button>
            </div>
        </div>`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

async function renderDayContent(date) {
    const items = await loadAgendaForDate(date);
    const cards = items.map(renderAgendaCard).join("");
    const addBtn = calendar.view !== "month"
        ? (canManage
            ? `<div class="add-zone" data-date="${toISODate(date)}">+ Item toevoegen</div>`
            : "")
        : items.slice(0, 3).map(i =>
            `<div class="mini-item">${escapeHtml(i.title)}</div>`
        ).join("");
    return cards + addBtn;
}

function showAgendaForm(item = null, defaultDate = null) {
    const isEdit = !!item;
    const anchorDate = item?.anchor_date || defaultDate || toISODate(new Date());
    const safeTitle = item ? escapeHtml(item.title) : "";
    showModal(`
        <h2>${isEdit ? "Agenda-item bewerken" : "Nieuw agenda-item"}</h2>
        <form id="agenda-form">
            <div class="form-group">
                <label for="agenda-anchor-date">Datum</label>
                <input type="date" id="agenda-anchor-date" name="anchor_date" required value="${escapeHtml(anchorDate)}">
            </div>
            <div class="form-group">
                <label for="agenda-title">Titel</label>
                <input type="text" id="agenda-title" name="title" required maxlength="200"
                    value="${safeTitle}">
            </div>
            ${repeatFieldsHtml(item || { repeat_type: "once" })}
            <div class="modal-actions">
                <button type="button" class="btn" onclick="hideModal()">Annuleren</button>
                <button type="submit" class="btn btn-primary">Opslaan</button>
            </div>
        </form>
    `);

    const form = document.getElementById("agenda-form");
    setupRepeatTypeToggle(form);

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            title: formFieldValue(form, "title"),
            anchor_date: formFieldValue(form, "anchor_date"),
            ...readRepeatFields(form),
        };

        if (isEdit) {
            await api(`/api/agenda/${item.id}`, { method: "PUT", body: JSON.stringify(payload) });
        } else {
            await api("/api/agenda", {
                method: "POST",
                body: JSON.stringify({ person_id: currentPersonId, ...payload }),
            });
        }
        hideModal();
        calendar.render();
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    const dropdown = document.getElementById("person-dropdown");
    const persons = await loadPersons();

    persons.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.name;
        dropdown.appendChild(opt);
    });

    if (persons.length > 0) {
        const me = await api("/api/me").catch(() => null);
        const preferred = persons.find(p => me && p.id === me.id) || persons[0];
        currentPersonId = preferred.id;
        dropdown.value = String(currentPersonId);
    }

    dropdown.addEventListener("change", async () => {
        currentPersonId = parseInt(dropdown.value);
        await refreshAccess();
    });

    const container = document.getElementById("calendar-container");

    calendar = new CalendarView(container, {
        draggable: false,
        renderDay: renderDayContent,
        onDateClick: (date) => {
            calendar.currentDate = date;
            calendar.setView("day");
        },
    });

    document.querySelectorAll(".view-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".view-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            calendar.setView(btn.dataset.view);
        });
    });

    document.getElementById("btn-prev").addEventListener("click", () => calendar.navigate(-1));
    document.getElementById("btn-next").addEventListener("click", () => calendar.navigate(1));
    document.getElementById("btn-today").addEventListener("click", () => calendar.goToday());

    container.addEventListener("click", async (e) => {
        if (e.target.closest(".add-zone")) {
            if (!canManage) {
                alert("Je hebt geen rechten om agenda-items te beheren voor deze gebruiker.");
                return;
            }
            const date = e.target.closest(".add-zone").dataset.date;
            showAgendaForm(null, date);
            return;
        }
        if (e.target.closest(".edit-agenda")) {
            if (!canManage) return;
            const id = parseInt(e.target.closest(".edit-agenda").dataset.id);
            const items = await loadAgendaForDate(calendar.currentDate);
            const item = items.find(i => i.id === id);
            if (item) showAgendaForm(item);
            return;
        }
        if (e.target.closest(".delete-agenda")) {
            if (!canManage) return;
            const id = e.target.closest(".delete-agenda").dataset.id;
            if (confirm("Item verwijderen?")) {
                await api(`/api/agenda/${id}`, { method: "DELETE" });
                calendar.render();
            }
        }
    });

    async function refreshAccess() {
        if (!currentPersonId) return;
        const access = await api(`/api/agenda/access?person_id=${currentPersonId}`);
        canManage = !!access.can_manage;
        calendar.render();
    }

    await refreshAccess();
});
