let calendar;
let currentPersonId = null;
let canManage = false;

async function loadTasksForDate(date) {
    const iso = toISODate(date);
    return api(`/api/tasks?date=${iso}&person_id=${currentPersonId}`);
}

function renderTaskCard(task) {
    const completed = task.completed ? "completed" : "";
    const disabled = canManage ? "" : "disabled-actions";
    return `
        <div class="task-card ${completed} ${disabled}" data-id="${task.id}" draggable="${canManage}">
            <span class="task-icon">${iconHtml(task.icon)}</span>
            <div class="task-info">
                <div class="task-date">${formatAnchorDate(task.anchor_date)}</div>
                <div class="task-title">${escapeHtml(task.title)}</div>
                <div class="task-desc">${escapeHtml(task.description)}</div>
            </div>
            <div class="task-actions">
                <button class="btn-small edit-task" data-id="${task.id}" ${canManage ? "" : "disabled"}>✎</button>
                <button class="btn-small delete-task" data-id="${task.id}" ${canManage ? "" : "disabled"}>✕</button>
            </div>
        </div>`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

async function renderDayContent(date) {
    const tasks = await loadTasksForDate(date);
    const cards = tasks.map(renderTaskCard).join("");
    const addBtn = calendar.view !== "month"
        ? `<div class="add-zone" data-date="${toISODate(date)}">+ Taak toevoegen</div>`
        : tasks.slice(0, 3).map(t =>
            `<div class="mini-item">${escapeHtml(t.title)}</div>`
        ).join("");
    return cards + addBtn;
}

function showTaskForm(task = null, defaultDate = null) {
    const isEdit = !!task;
    const anchorDate = task?.anchor_date || defaultDate || toISODate(new Date());
    const selectedIcon = normalizeIconId(task?.icon || "fas:circle-check");
    showModal(`
        <h2>${isEdit ? "Taak bewerken" : "Nieuwe taak"}</h2>
        <form id="task-form">
            <div class="form-group">
                <label>Datum</label>
                <input type="date" name="anchor_date" required value="${anchorDate}">
            </div>
            <div class="form-group">
                <label>Titel</label>
                <input type="text" name="title" required maxlength="200"
                    value="${task ? escapeHtml(task.title) : ""}">
            </div>
            <div class="form-group">
                <label>Beschrijving</label>
                <textarea name="description" maxlength="1000">${task ? escapeHtml(task.description) : ""}</textarea>
            </div>
            <div class="form-group">
                <label>Icoon</label>
                <div id="icon-picker-container">
                    ${createIconPicker(selectedIcon)}
                </div>
            </div>
            ${repeatFieldsHtml(task || { repeat_type: "once" })}
            <div class="modal-actions">
                <button type="button" class="btn" onclick="hideModal()">Annuleren</button>
                <button type="submit" class="btn btn-primary">Opslaan</button>
            </div>
        </form>
    `);

    const form = document.getElementById("task-form");
    initIconPicker(document.getElementById("icon-picker-container"));
    setupRepeatTypeToggle(form);

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            title: form.title.value,
            description: form.description.value,
            icon: form.icon.value,
            anchor_date: form.anchor_date.value,
            ...readRepeatFields(form),
        };

        if (isEdit) {
            await api(`/api/tasks/${task.id}`, { method: "PUT", body: JSON.stringify(payload) });
        } else {
            await api(`/api/tasks?person_id=${currentPersonId}`, { method: "POST", body: JSON.stringify(payload) });
        }
        hideModal();
        calendar.render();
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("calendar-container");
    const personSelect = document.getElementById("task-person-dropdown");
    const newBtn = document.getElementById("btn-new-task");

    calendar = new CalendarView(container, {
        draggable: true,
        renderDay: renderDayContent,
        onReorder: async (dateStr, taskIds) => {
            if (!canManage) return;
            await api(`/api/tasks/reorder?person_id=${currentPersonId}`, {
                method: "PUT",
                body: JSON.stringify({ date: dateStr, task_ids: taskIds }),
            });
        },
        onMove: async (taskId, fromDate, toDate, taskIds) => {
            if (!canManage) return;
            try {
                await api("/api/tasks/move", {
                    method: "PUT",
                    body: JSON.stringify({
                        task_id: taskId,
                        from_date: fromDate,
                        to_date: toDate,
                    }),
                });
                await api(`/api/tasks/reorder?person_id=${currentPersonId}`, {
                    method: "PUT",
                    body: JSON.stringify({ date: toDate, task_ids: taskIds }),
                });
            } finally {
                calendar.render();
            }
        },
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
    newBtn.addEventListener("click", () => {
        if (!canManage) {
            alert("Je hebt geen rechten om taken te beheren voor deze gebruiker.");
            return;
        }
        showTaskForm(null, toISODate(calendar.currentDate));
    });

    container.addEventListener("click", async (e) => {
        if (e.target.closest(".add-zone")) {
            const date = e.target.closest(".add-zone").dataset.date;
            if (!canManage) {
                alert("Je hebt geen rechten om taken te beheren voor deze gebruiker.");
                return;
            }
            showTaskForm(null, date);
            return;
        }
        if (e.target.closest(".edit-task")) {
            if (!canManage) return;
            const id = parseInt(e.target.closest(".edit-task").dataset.id);
            const task = await api(`/api/tasks/${id}`);
            if (task) showTaskForm(task);
            return;
        }
        if (e.target.closest(".delete-task")) {
            if (!canManage) return;
            const id = e.target.closest(".delete-task").dataset.id;
            if (confirm("Taak verwijderen?")) {
                await api(`/api/tasks/${id}`, { method: "DELETE" });
                calendar.render();
            }
        }
    });

    const observer = new MutationObserver(() => {
        if (!canManage) return;
        container.querySelectorAll(".task-card").forEach(card => calendar.makeDraggable(card));
    });
    observer.observe(container, { childList: true, subtree: true });

    async function loadPersons() {
        const persons = (await api("/api/persons")).filter(p => p.tasks_enabled);
        if (!persons.length) {
            personSelect.innerHTML = '<option value="">Geen gebruikers met takensysteem</option>';
            currentPersonId = null;
            newBtn.disabled = true;
            calendar.render();
            return;
        }
        personSelect.innerHTML = persons.map(p =>
            `<option value="${p.id}">${escapeHtml(p.name)}</option>`
        ).join("");
        const me = await api("/api/me").catch(() => null);
        const preferred = persons.find(p => me && p.id === me.id) || persons[0];
        currentPersonId = preferred.id;
        personSelect.value = String(currentPersonId);
        await refreshAccess();
    }

    async function refreshAccess() {
        if (!currentPersonId) return;
        const access = await api(`/api/tasks/access?person_id=${currentPersonId}`);
        canManage = !!access.can_manage;
        newBtn.disabled = !canManage;
        calendar.draggable = canManage;
        calendar.render();
    }

    personSelect.addEventListener("change", async () => {
        currentPersonId = parseInt(personSelect.value);
        await refreshAccess();
    });

    loadPersons();
});
