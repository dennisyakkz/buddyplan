function createIconPicker(selectedId = "fas:circle-check", inputName = "icon") {
    const normalized = normalizeIconId(selectedId);
    const hidden = `<input type="hidden" name="${inputName}" id="icon-input" value="${normalized}">`;
    const trigger = `
        <div class="icon-picker-trigger" id="icon-trigger">
            <span id="icon-preview">${iconHtml(normalized)}</span>
            <span id="icon-label">Icoon kiezen</span>
        </div>
        <div class="icon-picker-panel hidden" id="icon-panel">
            <input type="text" class="icon-picker-search" id="icon-search" placeholder="Zoek icoon (bijv. tanden, huis, sport)...">
            <div class="icon-picker-grid" id="icon-grid"></div>
        </div>
    `;

    return hidden + trigger;
}

async function initIconPicker(container) {
    await loadIcons();

    const input = container.querySelector("#icon-input");
    const trigger = container.querySelector("#icon-trigger");
    const panel = container.querySelector("#icon-panel");
    const search = container.querySelector("#icon-search");
    const grid = container.querySelector("#icon-grid");
    const preview = container.querySelector("#icon-preview");
    const label = container.querySelector("#icon-label");

    label.textContent = iconLabel(input.value);

    function renderGrid(filter = "") {
        const q = filter.toLowerCase().trim();
        const items = q
            ? ICONS.filter(i => iconSearchText(i).includes(q))
            : ICONS;

        const max = q ? items.length : 120;
        grid.innerHTML = items.slice(0, max).map(i => `
            <div class="icon-picker-item ${i.id === input.value ? "selected" : ""}" data-id="${i.id}" title="${escapeHtml(i.label)}">
                ${iconHtml(i.id)}
                <span>${escapeHtml(i.label)}</span>
            </div>
        `).join("");

        if (!q && ICONS.length > max) {
            grid.innerHTML += `<div class="icon-picker-hint">Typ om te zoeken in ${ICONS.length} iconen</div>`;
        }

        grid.querySelectorAll(".icon-picker-item").forEach(item => {
            item.addEventListener("click", () => {
                input.value = item.dataset.id;
                preview.innerHTML = iconHtml(item.dataset.id);
                label.textContent = iconLabel(item.dataset.id);
                panel.classList.add("hidden");
                grid.querySelectorAll(".icon-picker-item").forEach(el =>
                    el.classList.toggle("selected", el.dataset.id === item.dataset.id));
            });
        });
    }

    trigger.addEventListener("click", () => {
        panel.classList.toggle("hidden");
        if (!panel.classList.contains("hidden")) {
            search.value = "";
            renderGrid();
            search.focus();
        }
    });

    search.addEventListener("input", () => renderGrid(search.value));
    renderGrid();
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
