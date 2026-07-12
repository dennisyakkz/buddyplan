function todayIso() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
}

function mondayIsoOf(dateIso) {
    const d = new Date(dateIso + "T00:00:00");
    const dow = (d.getDay() + 6) % 7;
    d.setDate(d.getDate() - dow);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${dd}`;
}

function addDays(iso, n) {
    const d = new Date(iso + "T00:00:00");
    d.setDate(d.getDate() + n);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${dd}`;
}

function renderTodoTile(task) {
    const completed = task.completed ? "completed" : "";
    const icon = iconHtml(task.icon);
    const title = escapeHtml(task.title);
    const desc = escapeHtml(task.description || "");
    return `
        <div class="todo-tile ${completed}" data-id="${task.id}">
            <div class="todo-icon">${icon}</div>
            <div>
                <div class="todo-title">${title}</div>
                <div class="todo-desc">${desc}</div>
            </div>
        </div>
    `;
}

function contrastColor(hex) {
    if (!hex || hex.length < 7) return "#000000";
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    return (0.299 * r + 0.587 * g + 0.114 * b) > 0.5 ? "#000000" : "#ffffff";
}

function renderCalItem(item) {
    const text = typeof item === "string" ? item : (item.text || "");
    const color = typeof item === "object" ? (item.color || "") : "";
    if (color) {
        const fg = contrastColor(color);
        return `<span class="cal-chip" style="background:${escapeHtml(color)};color:${fg}">${escapeHtml(text)}</span>`;
    }
    return `<span class="cal-chip">${escapeHtml(text)}</span>`;
}

function renderWeekGrid(data) {
    const weekDays = data.weekDays || [];
    const people = data.calendar || [];
    const today = todayIso();

    const header = [
        `<div class="week-cell header"></div>`,
        ...weekDays.map(d => {
            const isToday = d.iso === today;
            return `<div class="week-cell header${isToday ? " today" : ""}">${escapeHtml(d.day)}<br><span>${escapeHtml(d.date)}</span></div>`;
        }),
    ].join("");

    const DAY_KEYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"];
    const rows = people.map(p => {
        const name = `<div class="week-cell name">${escapeHtml(p.name)}</div>`;
        const days = DAY_KEYS.map((k, i) => {
            const isToday = weekDays[i]?.iso === today;
            const chips = (p[k] || []).map(renderCalItem).join("");
            return `<div class="week-cell${isToday ? " today" : ""}">${chips}</div>`;
        }).join("");
        return name + days;
    }).join("");

    return `<div class="week-grid">${header}${rows}</div>`;
}

let currentWeekStart = null;
let currentMe = null;

async function renderCalendar() {
    const week = document.getElementById("dashboard-week");
    const weekData = await api(`/api/dashboard?start_date=${currentWeekStart}`);
    week.innerHTML = renderWeekGrid(weekData);
}

async function loadDashboard() {
    currentMe = await api("/api/me");
    currentWeekStart = mondayIsoOf(todayIso());

    const grid = document.getElementById("dashboard-grid");
    const leftPanel = document.getElementById("dashboard-left");
    const list = document.getElementById("dashboard-todo-list");
    const empty = document.getElementById("dashboard-todo-empty");

    await renderCalendar();

    if (!currentMe.tasks_enabled) {
        grid?.classList.add("single");
        leftPanel?.classList.add("hidden");
        return;
    }

    grid?.classList.remove("single");
    leftPanel?.classList.remove("hidden");

    const iso = todayIso();
    const tasks = await api(`/api/tasks?date=${iso}&person_id=${currentMe.id}`);
    if (!tasks.length) {
        empty.classList.remove("hidden");
        list.innerHTML = "";
    } else {
        empty.classList.add("hidden");
        list.innerHTML = tasks.map(renderTodoTile).join("");
    }

    if (!list) return;
    list.addEventListener("click", async (e) => {
        const tile = e.target.closest(".todo-tile");
        if (!tile) return;
        const id = tile.dataset.id;
        const task = tasks.find(t => String(t.id) === String(id));
        if (!task || task.completed) return;

        showModal(`
            <h2>${escapeHtml(task.title)}</h2>
            <p>${escapeHtml(task.description || "")}</p>
            <div class="modal-actions">
                <button type="button" class="btn" onclick="hideModal()">Sluiten</button>
                <button type="button" class="btn btn-primary" id="btn-dashboard-done">Ik heb het uitgevoerd</button>
            </div>
        `);
        document.getElementById("btn-dashboard-done").addEventListener("click", async () => {
            await api(`/api/tasks/${task.id}/complete?date=${iso}`, { method: "POST" });
            hideModal();
            await loadDashboard();
        });
    }, { once: true });
}

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard().catch(err => {
        console.error(err);
        showModal(`<h2>Fout</h2><p>${escapeHtml(err.message || String(err))}</p>`);
    });

    document.getElementById("cal-prev")?.addEventListener("click", async () => {
        currentWeekStart = addDays(currentWeekStart, -7);
        await renderCalendar();
    });

    document.getElementById("cal-next")?.addEventListener("click", async () => {
        currentWeekStart = addDays(currentWeekStart, 7);
        await renderCalendar();
    });

    document.getElementById("cal-today")?.addEventListener("click", async () => {
        currentWeekStart = mondayIsoOf(todayIso());
        await renderCalendar();
    });
});
