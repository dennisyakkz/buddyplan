let ICONS = [];
let iconsLoaded = false;

const LEGACY_ICON_MAP = {
    toothbrush: "fas:tooth",
    shower: "fas:shower",
    food: "fas:utensils",
    home: "fas:house",
    book: "fas:book",
    music: "fas:music",
    walk: "fas:person-walking",
    clothes: "fas:shirt",
    water: "fas:glass-water",
    bed: "fas:bed",
    default: "fas:circle-check",
};

async function loadIcons() {
    if (iconsLoaded) return ICONS;
    ICONS = await api("/api/icons");
    iconsLoaded = true;
    return ICONS;
}

function normalizeIconId(iconId) {
    if (!iconId) return LEGACY_ICON_MAP.default;
    if (iconId.startsWith("fas:")) return iconId;
    return LEGACY_ICON_MAP[iconId] || `fas:${iconId}`;
}

function iconNameFromId(iconId) {
    return normalizeIconId(iconId).replace("fas:", "");
}

function iconHtml(iconId, extraClass = "") {
    const name = iconNameFromId(iconId);
    return `<i class="fa-solid fa-${name} fa-icon ${extraClass}"></i>`;
}

function iconLabel(iconId) {
    const normalized = normalizeIconId(iconId);
    const found = ICONS.find(i => i.id === normalized);
    return found ? found.label : iconNameFromId(iconId);
}

function iconSearchText(icon) {
    return [icon.label, icon.name, ...(icon.terms || [])].join(" ").toLowerCase();
}

const DUTCH_DAYS = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"];
const DUTCH_MONTHS = ["", "Januari", "Februari", "Maart", "April", "Mei", "Juni",
    "Juli", "Augustus", "September", "Oktober", "November", "December"];

function formatAnchorDate(iso) {
    if (!iso) return "";
    const d = new Date(iso + "T00:00:00");
    return formatDateNL(d);
}

function formatDateNL(d) {
    return `${d.getDate()} ${DUTCH_MONTHS[d.getMonth() + 1]}`;
}

function formatDayNL(d) {
    return DUTCH_DAYS[(d.getDay() + 6) % 7];
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
}

function toISODate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

function mondayOf(d) {
    const copy = new Date(d);
    const day = (copy.getDay() + 6) % 7;
    copy.setDate(copy.getDate() - day);
    copy.setHours(0, 0, 0, 0);
    return copy;
}

function isSameDay(a, b) {
    return a.getFullYear() === b.getFullYear() &&
        a.getMonth() === b.getMonth() &&
        a.getDate() === b.getDate();
}

function isToday(d) {
    return isSameDay(d, new Date());
}

async function api(path, options = {}) {
    const res = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fout: ${res.status}`);
    }
    if (res.status === 204) return null;
    return res.json();
}

function showModal(html) {
    const overlay = document.getElementById("modal-overlay");
    const content = document.getElementById("modal-content");
    content.innerHTML = html;
    overlay.classList.remove("hidden");
    overlay.onclick = (e) => {
        if (e.target === overlay) hideModal();
    };
    content.onclick = (e) => e.stopPropagation();
}

function hideModal() {
    document.getElementById("modal-overlay").classList.add("hidden");
}

function formFieldValue(form, name) {
    const el = form.elements.namedItem(name);
    return el && "value" in el ? el.value : "";
}

function repeatTypeOptions(selected = "once") {
    const types = [
        { value: "once", label: "Eenmalig" },
        { value: "daily", label: "Dagelijks" },
        { value: "weekly", label: "Wekelijks" },
        { value: "biweekly", label: "Twee wekelijks" },
        { value: "weekdays", label: "Dagen van de week" },
    ];
    return types.map(t =>
        `<option value="${t.value}" ${t.value === selected ? "selected" : ""}>${t.label}</option>`
    ).join("");
}

function weekdayChecks(selected = [], name = "weekdays") {
    return DUTCH_DAYS.map((day, i) => `
        <label>
            <input type="checkbox" name="${name}" value="${i}" ${selected.includes(i) ? "checked" : ""}>
            ${day.slice(0, 2)}
        </label>
    `).join("");
}

function getSelectedWeekdays(form) {
    return Array.from(form.querySelectorAll('input[name="weekdays"]:checked'))
        .map(cb => parseInt(cb.value));
}

function repeatFieldsHtml(data = {}) {
    const repeatType = data.repeat_type || "once";
    const weekdays = Array.isArray(data.repeat_weekdays) ? data.repeat_weekdays : [];
    const endDate = data.end_date || "";
    return `
        <div class="form-group">
            <label for="repeat-type">Herhaling</label>
            <select name="repeat_type" id="repeat-type">${repeatTypeOptions(repeatType)}</select>
        </div>
        <div class="form-group" id="weekdays-group">
            <label>Dagen</label>
            <div class="weekday-checks">${weekdayChecks(weekdays)}</div>
        </div>
        <div class="form-group" id="end-date-group">
            <label for="agenda-end-date">Einddatum (optioneel)</label>
            <input type="date" id="agenda-end-date" name="end_date" value="${escapeHtml(String(endDate))}">
        </div>
    `;
}

function setupRepeatTypeToggle(form) {
    if (!form) return;
    const select = form.querySelector("#repeat-type");
    const weekdaysGroup = form.querySelector("#weekdays-group");
    const endDateGroup = form.querySelector("#end-date-group");
    if (!select || !weekdaysGroup || !endDateGroup) return;

    function update() {
        const val = select.value;
        weekdaysGroup.style.display = val === "weekdays" ? "block" : "none";
        endDateGroup.style.display = val === "once" ? "none" : "block";
    }
    select.addEventListener("change", update);
    update();
}

function readRepeatFields(form) {
    return {
        repeat_type: formFieldValue(form, "repeat_type"),
        repeat_weekdays: getSelectedWeekdays(form),
        end_date: formFieldValue(form, "end_date") || null,
    };
}
